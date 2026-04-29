from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import json
from django.conf import settings
from pathlib import Path


from student_management_app.models import CustomUser, Staffs, Courses, Subjects, Students, SessionYearModel, Attendance, AttendanceReport, LeaveReportStaff, FeedBackStaffs, StudentResult, Syllabus, Module, CourseObjective, CO_PO_Mapping, ApprovalLog
from student_management_app.forms import SyllabusForm
from django.template.loader import get_template


def staff_home(request):
    # Fetching All Students under Staff

    subjects = Subjects.objects.filter(staff_id=request.user.id)
    course_id_list = []
    for subject in subjects:
        course = Courses.objects.get(id=subject.course_id.id)
        course_id_list.append(course.id)
    
    final_course = []
    # Removing Duplicate Course Id
    for course_id in course_id_list:
        if course_id not in final_course:
            final_course.append(course_id)
    
    students_count = Students.objects.filter(course_id__in=final_course).count()
    subject_count = subjects.count()

    # Fetch All Attendance Count
    attendance_count = Attendance.objects.filter(subject_id__in=subjects).count()
    # Fetch All Approve Leave
    staff = Staffs.objects.get(admin=request.user.id)
    leave_count = LeaveReportStaff.objects.filter(staff_id=staff.id, leave_status=1).count()

    #Fetch Attendance Data by Subjects
    subject_list = []
    attendance_list = []
    for subject in subjects:
        attendance_count1 = Attendance.objects.filter(subject_id=subject.id).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count1)

    students_attendance = Students.objects.filter(course_id__in=final_course)
    student_list = []
    student_list_attendance_present = []
    student_list_attendance_absent = []
    for student in students_attendance:
        attendance_present_count = AttendanceReport.objects.filter(status=True, student_id=student.id).count()
        attendance_absent_count = AttendanceReport.objects.filter(status=False, student_id=student.id).count()
        student_list.append(student.admin.first_name+" "+ student.admin.last_name)
        student_list_attendance_present.append(attendance_present_count)
        student_list_attendance_absent.append(attendance_absent_count)

    context={
        "students_count": students_count,
        "attendance_count": attendance_count,
        "leave_count": leave_count,
        "subject_count": subject_count,
        "subject_list": subject_list,
        "attendance_list": attendance_list,
        "student_list": student_list,
        "attendance_present_list": student_list_attendance_present,
        "attendance_absent_list": student_list_attendance_absent
    }
    return render(request, "staff_template/staff_home_template.html", context)


def staff_syllabus_list(request):
    if request.user.user_type != '2':
        messages.error(request, "Unauthorized access")
        return redirect('staff_home')

    staff = Staffs.objects.get(admin=request.user.id)
    syllabi = Syllabus.objects.filter(created_by=staff).order_by('-created_at')
    return render(request, "staff_template/manage_syllabus.html", {"syllabi": syllabi})


def staff_generate_pdf(request, syllabus_id):
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse("WeasyPrint is not installed. Install it in the active environment.")

    staff = Staffs.objects.get(admin=request.user.id)
    syllabus = get_object_or_404(Syllabus, id=syllabus_id, created_by=staff)
    modules = Module.objects.filter(syllabus=syllabus).order_by('order')
    total_hours = sum(module.teaching_hours for module in modules)
    course_objectives = CourseObjective.objects.filter(syllabus=syllabus).order_by('id')
    mappings = CO_PO_Mapping.objects.filter(syllabus=syllabus)
    mapping_matrix = _build_mapping_matrix(syllabus, course_objectives, mappings)
    textbook_rows = _parse_resource_rows(syllabus.textbooks)
    reference_rows = _parse_resource_rows(syllabus.reference_books)
    web_links = _parse_simple_list(syllabus.web_links)
    activity_items = _parse_simple_list(syllabus.activity_learning)

    template = get_template("hod_template/syllabus_pdf.html")
    logo_path = Path(settings.MEDIA_ROOT) / "image.png"
    html = template.render({
        "syllabus": syllabus,
        "modules": modules,
        "course_objectives": course_objectives,
        "mapping_matrix": mapping_matrix,
        "po_count": syllabus.po_count,
        "pso_count": syllabus.pso_count,
        "total_hours": total_hours,
        "logo_url": logo_path.as_uri() if logo_path.exists() else "",
        "textbook_rows": textbook_rows,
        "reference_rows": reference_rows,
        "web_links": web_links,
        "activity_items": activity_items,
    })

    response = HttpResponse(content_type='application/pdf')
    if request.GET.get('download'):
        response['Content-Disposition'] = 'attachment; filename="syllabus.pdf"'
    else:
        response['Content-Disposition'] = 'inline; filename="syllabus.pdf"'

    pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()
    response.write(pdf)
    return response


def staff_syllabus_create(request):
    if request.user.user_type != '2':
        messages.error(request, "Unauthorized access")
        return redirect('staff_home')

    staff = Staffs.objects.get(admin=request.user.id)
    subject_queryset = Subjects.objects.filter(staff_id=request.user.id)

    if request.method == "POST":
        form = SyllabusForm(request.POST)
        form.fields['subject'].queryset = subject_queryset
        if form.is_valid():
            subject = form.cleaned_data['subject']
            syllabus = form.save(commit=False)
            syllabus.created_by = staff
            if subject.course_id:
                syllabus.subject = subject
            syllabus.textbooks = _serialize_resource_rows(request.POST, "textbook")
            syllabus.reference_books = _serialize_resource_rows(request.POST, "reference")
            syllabus.web_links = _serialize_simple_list(request.POST, "web_link")
            syllabus.activity_learning = _serialize_simple_list(request.POST, "activity_item")
            action = request.POST.get("action")
            if action == "submit":
                syllabus.status = "faculty_approved"
            else:
                syllabus.status = "draft"
            syllabus.save()

            _save_course_objectives(syllabus, request.POST)
            _save_modules(syllabus, request.POST)
            _save_co_po_mappings(syllabus, request.POST)

            if action == "submit":
                ApprovalLog.objects.create(
                    syllabus=syllabus,
                    action="submit",
                    from_status="draft",
                    to_status="faculty_approved",
                    approver=request.user,
                    comment=request.POST.get("approval_comment", "")
                )
                messages.success(request, "Syllabus submitted for approval")
            else:
                messages.success(request, "Syllabus saved as draft")
            return redirect('staff_syllabus_list')
    else:
        form = SyllabusForm()
        form.fields['subject'].queryset = subject_queryset
    if request.method == "POST":
        resource_context = {
            "textbook_rows": _extract_resource_rows(request.POST, "textbook"),
            "reference_rows": _extract_resource_rows(request.POST, "reference"),
            "web_links": _extract_simple_list(request.POST, "web_link"),
            "activity_items": _extract_simple_list(request.POST, "activity_item"),
        }
    else:
        resource_context = {
            "textbook_rows": [],
            "reference_rows": [],
            "web_links": [],
            "activity_items": [],
        }

    return render(request, "staff_template/create_syllabus.html", {"form": form, **resource_context})


def staff_syllabus_edit(request, syllabus_id):
    if request.user.user_type != '2':
        messages.error(request, "Unauthorized access")
        return redirect('staff_home')

    staff = Staffs.objects.get(admin=request.user.id)
    syllabus = Syllabus.objects.get(id=syllabus_id, created_by=staff)
    previous_status = syllabus.status

    subject_queryset = Subjects.objects.filter(staff_id=request.user.id)

    if request.method == "POST":
        form = SyllabusForm(request.POST, instance=syllabus)
        form.fields['subject'].queryset = subject_queryset
        if form.is_valid():
            syllabus = form.save(commit=False)
            syllabus.textbooks = _serialize_resource_rows(request.POST, "textbook")
            syllabus.reference_books = _serialize_resource_rows(request.POST, "reference")
            syllabus.web_links = _serialize_simple_list(request.POST, "web_link")
            syllabus.activity_learning = _serialize_simple_list(request.POST, "activity_item")
            syllabus.save()

            CourseObjective.objects.filter(syllabus=syllabus).delete()
            Module.objects.filter(syllabus=syllabus).delete()
            CO_PO_Mapping.objects.filter(syllabus=syllabus).delete()

            _save_course_objectives(syllabus, request.POST)
            _save_modules(syllabus, request.POST)
            _save_co_po_mappings(syllabus, request.POST)

            if previous_status != "draft":
                syllabus.status = "draft"
                syllabus.save(update_fields=["status"])
                ApprovalLog.objects.create(
                    syllabus=syllabus,
                    action="submit",
                    from_status=previous_status,
                    to_status="draft",
                    approver=request.user,
                    comment="Revised by staff"
                )
                messages.success(request, "Syllabus revised. Please submit again for approval.")
            else:
                messages.success(request, "Syllabus updated")
            return redirect('staff_syllabus_list')
    else:
        form = SyllabusForm(instance=syllabus)
        form.fields['subject'].queryset = subject_queryset

    mapping_data = _build_mapping_data(syllabus)
    if request.method == "POST":
        resource_context = {
            "textbook_rows": _extract_resource_rows(request.POST, "textbook"),
            "reference_rows": _extract_resource_rows(request.POST, "reference"),
            "web_links": _extract_simple_list(request.POST, "web_link"),
            "activity_items": _extract_simple_list(request.POST, "activity_item"),
        }
    else:
        resource_context = {
            "textbook_rows": _parse_resource_rows(syllabus.textbooks),
            "reference_rows": _parse_resource_rows(syllabus.reference_books),
            "web_links": _parse_simple_list(syllabus.web_links),
            "activity_items": _parse_simple_list(syllabus.activity_learning),
        }
    context = {
        "form": form,
        "syllabus": syllabus,
        "modules": Module.objects.filter(syllabus=syllabus).order_by('order'),
        "course_objectives": CourseObjective.objects.filter(syllabus=syllabus).order_by('id'),
        "mapping_data": mapping_data,
        **resource_context,
    }
    return render(request, "staff_template/create_syllabus.html", context)


def staff_syllabus_submit(request, syllabus_id):
    if request.user.user_type != '2':
        messages.error(request, "Unauthorized access")
        return redirect('staff_home')

    staff = Staffs.objects.get(admin=request.user.id)
    syllabus = Syllabus.objects.get(id=syllabus_id, created_by=staff)
    if syllabus.status != "draft":
        messages.error(request, "Only drafts can be submitted")
        return redirect('staff_syllabus_list')

    syllabus.status = "faculty_approved"
    syllabus.save()
    ApprovalLog.objects.create(
        syllabus=syllabus,
        action="submit",
        from_status="draft",
        to_status="faculty_approved",
        approver=request.user,
        comment=request.POST.get("approval_comment", "")
    )
    messages.success(request, "Syllabus submitted for approval")
    return redirect('staff_syllabus_list')


def _save_course_objectives(syllabus, post_data):
    descriptions = post_data.getlist("co_description")
    for index, description in enumerate(descriptions, start=1):
        description = description.strip()
        if not description:
            continue
        CourseObjective.objects.create(
            syllabus=syllabus,
            co_code="CO{0}".format(index),
            description=description
        )


def _save_modules(syllabus, post_data):
    module_names = post_data.getlist("module_name")
    contents = post_data.getlist("module_content")
    teaching_hours = post_data.getlist("module_hours")
    hands_on = post_data.getlist("module_hands_on")
    self_learning = post_data.getlist("module_self_learning")
    rbt_levels = post_data.getlist("module_rbt")
    books_refs = post_data.getlist("module_refs")

    for index, module_name in enumerate(module_names):
        module_name = module_name.strip()
        if not module_name:
            continue
        Module.objects.create(
            syllabus=syllabus,
            module_name=module_name,
            content=_safe_list_get(contents, index),
            teaching_hours=_safe_int(_safe_list_get(teaching_hours, index)),
            hands_on_exercises=_safe_list_get(hands_on, index),
            self_learning=_safe_list_get(self_learning, index),
            rbt_level=_safe_list_get(rbt_levels, index),
            books_references=_safe_list_get(books_refs, index),
            order=index + 1
        )


def _save_co_po_mappings(syllabus, post_data):
    co_list = list(CourseObjective.objects.filter(syllabus=syllabus).order_by('id'))
    po_count = int(post_data.get("po_count", syllabus.po_count or 12))
    pso_count = int(post_data.get("pso_count", syllabus.pso_count or 3))
    for co_index, co in enumerate(co_list, start=1):
        for po_index in range(1, po_count + 1):
            value = post_data.get("map_co{0}_po{1}".format(co_index, po_index))
            if value in ["1", "2", "3"]:
                CO_PO_Mapping.objects.create(
                    syllabus=syllabus,
                    course_objective=co,
                    outcome_type="PO",
                    outcome_number=po_index,
                    mapping_level=int(value)
                )
        for pso_index in range(1, pso_count + 1):
            value = post_data.get("map_co{0}_pso{1}".format(co_index, pso_index))
            if value in ["1", "2", "3"]:
                CO_PO_Mapping.objects.create(
                    syllabus=syllabus,
                    course_objective=co,
                    outcome_type="PSO",
                    outcome_number=pso_index,
                    mapping_level=int(value)
                )


def _build_mapping_matrix(syllabus, course_objectives, mappings):
    mapping_lookup = {}
    for mapping in mappings:
        key = (mapping.course_objective_id, mapping.outcome_type, mapping.outcome_number)
        mapping_lookup[key] = mapping.mapping_level

    matrix = []
    for co in course_objectives:
        row = {
            "co": co,
            "po_values": [],
            "pso_values": [],
        }
        for po_index in range(1, syllabus.po_count + 1):
            row["po_values"].append(mapping_lookup.get((co.id, "PO", po_index), ""))
        for pso_index in range(1, syllabus.pso_count + 1):
            row["pso_values"].append(mapping_lookup.get((co.id, "PSO", pso_index), ""))
        matrix.append(row)
    return matrix


def _build_mapping_data(syllabus):
    mapping_data = {}
    co_list = list(CourseObjective.objects.filter(syllabus=syllabus).order_by('id'))
    co_index_lookup = {co.id: index + 1 for index, co in enumerate(co_list)}
    mappings = CO_PO_Mapping.objects.filter(syllabus=syllabus)

    for mapping in mappings:
        co_index = co_index_lookup.get(mapping.course_objective_id)
        if not co_index:
            continue
        co_key = "co{0}".format(co_index)
        if co_key not in mapping_data:
            mapping_data[co_key] = {}
        outcome_key = "{0}{1}".format(mapping.outcome_type, mapping.outcome_number)
        mapping_data[co_key][outcome_key] = mapping.mapping_level

    return json.dumps(mapping_data)


def _extract_resource_rows(post_data, prefix):
    titles = post_data.getlist("{0}_title".format(prefix))
    authors = post_data.getlist("{0}_author".format(prefix))
    editions = post_data.getlist("{0}_edition".format(prefix))
    publishers = post_data.getlist("{0}_publisher".format(prefix))

    rows = []
    max_len = max(len(titles), len(authors), len(editions), len(publishers), 0)
    for index in range(max_len):
        title = _safe_list_get(titles, index).strip()
        author = _safe_list_get(authors, index).strip()
        edition = _safe_list_get(editions, index).strip()
        publisher = _safe_list_get(publishers, index).strip()
        if not any([title, author, edition, publisher]):
            continue
        rows.append({
            "title": title,
            "author": author,
            "edition": edition,
            "publisher": publisher,
        })
    return rows


def _serialize_resource_rows(post_data, prefix):
    rows = _extract_resource_rows(post_data, prefix)
    lines = []
    for row in rows:
        lines.append("{0} | {1} | {2} | {3}".format(
            row["title"],
            row["author"],
            row["edition"],
            row["publisher"]
        ))
    return "\n".join(lines)


def _parse_resource_rows(text):
    rows = []
    if not text:
        return rows
    for line in text.splitlines():
        parts = [part.strip() for part in line.split("|")]
        while len(parts) < 4:
            parts.append("")
        if not any(parts):
            continue
        rows.append({
            "title": parts[0],
            "author": parts[1],
            "edition": parts[2],
            "publisher": parts[3],
        })
    return rows


def _extract_simple_list(post_data, key):
    return [item.strip() for item in post_data.getlist(key) if item.strip()]


def _serialize_simple_list(post_data, key):
    return "\n".join(_extract_simple_list(post_data, key))


def _parse_simple_list(text):
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def _safe_list_get(values, index):
    if index < len(values):
        return values[index]
    return ""


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0



def staff_take_attendance(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "staff_template/take_attendance_template.html", context)


def staff_apply_leave(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    leave_data = LeaveReportStaff.objects.filter(staff_id=staff_obj)
    context = {
        "leave_data": leave_data
    }
    return render(request, "staff_template/staff_apply_leave_template.html", context)


def staff_apply_leave_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('staff_apply_leave')
    else:
        leave_date = request.POST.get('leave_date')
        leave_message = request.POST.get('leave_message')

        staff_obj = Staffs.objects.get(admin=request.user.id)
        try:
            leave_report = LeaveReportStaff(staff_id=staff_obj, leave_date=leave_date, leave_message=leave_message, leave_status=0)
            leave_report.save()
            messages.success(request, "Applied for Leave.")
            return redirect('staff_apply_leave')
        except:
            messages.error(request, "Failed to Apply Leave")
            return redirect('staff_apply_leave')


def staff_feedback(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    feedback_data = FeedBackStaffs.objects.filter(staff_id=staff_obj)
    context = {
        "feedback_data":feedback_data
    }
    return render(request, "staff_template/staff_feedback_template.html", context)


def staff_feedback_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method.")
        return redirect('staff_feedback')
    else:
        feedback = request.POST.get('feedback_message')
        staff_obj = Staffs.objects.get(admin=request.user.id)

        try:
            add_feedback = FeedBackStaffs(staff_id=staff_obj, feedback=feedback, feedback_reply="")
            add_feedback.save()
            messages.success(request, "Feedback Sent.")
            return redirect('staff_feedback')
        except:
            messages.error(request, "Failed to Send Feedback.")
            return redirect('staff_feedback')


# WE don't need csrf_token when using Ajax
@csrf_exempt
def get_students(request):
    # Getting Values from Ajax POST 'Fetch Student'
    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year")

    # Students enroll to Course, Course has Subjects
    # Getting all data from subject model based on subject_id
    subject_model = Subjects.objects.get(id=subject_id)

    session_model = SessionYearModel.objects.get(id=session_year)

    students = Students.objects.filter(course_id=subject_model.course_id, session_year_id=session_model)

    # Only Passing Student Id and Student Name Only
    list_data = []

    for student in students:
        data_small={"id":student.admin.id, "name":student.admin.first_name+" "+student.admin.last_name}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)




@csrf_exempt
def save_attendance_data(request):
    # Get Values from Staf Take Attendance form via AJAX (JavaScript)
    # Use getlist to access HTML Array/List Input Data
    student_ids = request.POST.get("student_ids")
    subject_id = request.POST.get("subject_id")
    attendance_date = request.POST.get("attendance_date")
    session_year_id = request.POST.get("session_year_id")

    subject_model = Subjects.objects.get(id=subject_id)
    session_year_model = SessionYearModel.objects.get(id=session_year_id)

    json_student = json.loads(student_ids)
    # print(dict_student[0]['id'])

    # print(student_ids)
    try:
        # First Attendance Data is Saved on Attendance Model
        attendance = Attendance(subject_id=subject_model, attendance_date=attendance_date, session_year_id=session_year_model)
        attendance.save()

        for stud in json_student:
            # Attendance of Individual Student saved on AttendanceReport Model
            student = Students.objects.get(admin=stud['id'])
            attendance_report = AttendanceReport(student_id=student, attendance_id=attendance, status=stud['status'])
            attendance_report.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("Error")




def staff_update_attendance(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "staff_template/update_attendance_template.html", context)

@csrf_exempt
def get_attendance_dates(request):
    

    # Getting Values from Ajax POST 'Fetch Student'
    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year_id")

    # Students enroll to Course, Course has Subjects
    # Getting all data from subject model based on subject_id
    subject_model = Subjects.objects.get(id=subject_id)

    session_model = SessionYearModel.objects.get(id=session_year)

    # students = Students.objects.filter(course_id=subject_model.course_id, session_year_id=session_model)
    attendance = Attendance.objects.filter(subject_id=subject_model, session_year_id=session_model)

    # Only Passing Student Id and Student Name Only
    list_data = []

    for attendance_single in attendance:
        data_small={"id":attendance_single.id, "attendance_date":str(attendance_single.attendance_date), "session_year_id":attendance_single.session_year_id.id}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
def get_attendance_student(request):
    # Getting Values from Ajax POST 'Fetch Student'
    attendance_date = request.POST.get('attendance_date')
    attendance = Attendance.objects.get(id=attendance_date)

    attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
    # Only Passing Student Id and Student Name Only
    list_data = []

    for student in attendance_data:
        data_small={"id":student.student_id.admin.id, "name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name, "status":student.status}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
def update_attendance_data(request):
    student_ids = request.POST.get("student_ids")

    attendance_date = request.POST.get("attendance_date")
    attendance = Attendance.objects.get(id=attendance_date)

    json_student = json.loads(student_ids)

    try:
        
        for stud in json_student:
            # Attendance of Individual Student saved on AttendanceReport Model
            student = Students.objects.get(admin=stud['id'])

            attendance_report = AttendanceReport.objects.get(student_id=student, attendance_id=attendance)
            attendance_report.status=stud['status']

            attendance_report.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("Error")


def staff_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)

    context={
        "user": user,
        "staff": staff
    }
    return render(request, 'staff_template/staff_profile.html', context)


def staff_profile_update(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('staff_profile')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        address = request.POST.get('address')

        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()

            staff = Staffs.objects.get(admin=customuser.id)
            staff.address = address
            staff.save()

            messages.success(request, "Profile Updated Successfully")
            return redirect('staff_profile')
        except:
            messages.error(request, "Failed to Update Profile")
            return redirect('staff_profile')



def staff_add_result(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years,
    }
    return render(request, "staff_template/add_result_template.html", context)


def staff_add_result_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('staff_add_result')
    else:
        student_admin_id = request.POST.get('student_list')
        assignment_marks = request.POST.get('assignment_marks')
        exam_marks = request.POST.get('exam_marks')
        subject_id = request.POST.get('subject')

        student_obj = Students.objects.get(admin=student_admin_id)
        subject_obj = Subjects.objects.get(id=subject_id)

        try:
            # Check if Students Result Already Exists or not
            check_exist = StudentResult.objects.filter(subject_id=subject_obj, student_id=student_obj).exists()
            if check_exist:
                result = StudentResult.objects.get(subject_id=subject_obj, student_id=student_obj)
                result.subject_assignment_marks = assignment_marks
                result.subject_exam_marks = exam_marks
                result.save()
                messages.success(request, "Result Updated Successfully!")
                return redirect('staff_add_result')
            else:
                result = StudentResult(student_id=student_obj, subject_id=subject_obj, subject_exam_marks=exam_marks, subject_assignment_marks=assignment_marks)
                result.save()
                messages.success(request, "Result Added Successfully!")
                return redirect('staff_add_result')
        except:
            messages.error(request, "Failed to Add Result!")
            return redirect('staff_add_result')
