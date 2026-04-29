from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.urls import reverse
import datetime # To Parse input DateTime into Python Date Time Object
from django.conf import settings
from pathlib import Path

from student_management_app.models import CustomUser, Staffs, Courses, Subjects, Students, Attendance, AttendanceReport, LeaveReportStudent, FeedBackStudent, StudentResult, Syllabus, Module, CourseObjective, CO_PO_Mapping
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from django.shortcuts import render

def student_syllabus(request):
    syllabus = Syllabus.objects.filter(status="hod_approved")
    return render(request, "student_template/student_syllabus.html", {"syllabus": syllabus})


def student_generate_pdf(request, syllabus_id):
    try:
        from weasyprint import HTML
    except ImportError:
        return HttpResponse("WeasyPrint is not installed. Install it in the active environment.")

    syllabus = get_object_or_404(Syllabus, id=syllabus_id, status="hod_approved")
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


def _parse_simple_list(text):
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]

def student_home(request):
    student_obj = Students.objects.get(admin=request.user.id)
    total_attendance = AttendanceReport.objects.filter(student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(student_id=student_obj, status=False).count()

    course_obj = Courses.objects.get(id=student_obj.course_id.id)
    total_subjects = Subjects.objects.filter(course_id=course_obj).count()

    subject_name = []
    data_present = []
    data_absent = []
    subject_data = Subjects.objects.filter(course_id=student_obj.course_id)
    for subject in subject_data:
        attendance = Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=True, student_id=student_obj.id).count()
        attendance_absent_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=False, student_id=student_obj.id).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)
    
    context={
        "total_attendance": total_attendance,
        "attendance_present": attendance_present,
        "attendance_absent": attendance_absent,
        "total_subjects": total_subjects,
        "subject_name": subject_name,
        "data_present": data_present,
        "data_absent": data_absent
    }
    return render(request, "student_template/student_home_template.html", context)


def student_view_attendance(request):
    student = Students.objects.get(admin=request.user.id) # Getting Logged in Student Data
    course = student.course_id # Getting Course Enrolled of LoggedIn Student
    # course = Courses.objects.get(id=student.course_id.id) # Getting Course Enrolled of LoggedIn Student
    subjects = Subjects.objects.filter(course_id=course) # Getting the Subjects of Course Enrolled
    context = {
        "subjects": subjects
    }
    return render(request, "student_template/student_view_attendance.html", context)


def student_view_attendance_post(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('student_view_attendance')
    else:
        # Getting all the Input Data
        subject_id = request.POST.get('subject')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Parsing the date data into Python object
        start_date_parse = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_parse = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

        # Getting all the Subject Data based on Selected Subject
        subject_obj = Subjects.objects.get(id=subject_id)
        # Getting Logged In User Data
        user_obj = CustomUser.objects.get(id=request.user.id)
        # Getting Student Data Based on Logged in Data
        stud_obj = Students.objects.get(admin=user_obj)

        # Now Accessing Attendance Data based on the Range of Date Selected and Subject Selected
        attendance = Attendance.objects.filter(attendance_date__range=(start_date_parse, end_date_parse), subject_id=subject_obj)
        # Getting Attendance Report based on the attendance details obtained above
        attendance_reports = AttendanceReport.objects.filter(attendance_id__in=attendance, student_id=stud_obj)

        # for attendance_report in attendance_reports:
        #     print("Date: "+ str(attendance_report.attendance_id.attendance_date), "Status: "+ str(attendance_report.status))

        # messages.success(request, "Attendacne View Success")

        context = {
            "subject_obj": subject_obj,
            "attendance_reports": attendance_reports
        }

        return render(request, 'student_template/student_attendance_data.html', context)
       

def student_apply_leave(request):
    student_obj = Students.objects.get(admin=request.user.id)
    leave_data = LeaveReportStudent.objects.filter(student_id=student_obj)
    context = {
        "leave_data": leave_data
    }
    return render(request, 'student_template/student_apply_leave.html', context)


def student_apply_leave_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('student_apply_leave')
    else:
        leave_date = request.POST.get('leave_date')
        leave_message = request.POST.get('leave_message')

        student_obj = Students.objects.get(admin=request.user.id)
        try:
            leave_report = LeaveReportStudent(student_id=student_obj, leave_date=leave_date, leave_message=leave_message, leave_status=0)
            leave_report.save()
            messages.success(request, "Applied for Leave.")
            return redirect('student_apply_leave')
        except:
            messages.error(request, "Failed to Apply Leave")
            return redirect('student_apply_leave')


def student_feedback(request):
    student_obj = Students.objects.get(admin=request.user.id)
    feedback_data = FeedBackStudent.objects.filter(student_id=student_obj)
    context = {
        "feedback_data": feedback_data
    }
    return render(request, 'student_template/student_feedback.html', context)


def student_feedback_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method.")
        return redirect('student_feedback')
    else:
        feedback = request.POST.get('feedback_message')
        student_obj = Students.objects.get(admin=request.user.id)

        try:
            add_feedback = FeedBackStudent(student_id=student_obj, feedback=feedback, feedback_reply="")
            add_feedback.save()
            messages.success(request, "Feedback Sent.")
            return redirect('student_feedback')
        except:
            messages.error(request, "Failed to Send Feedback.")
            return redirect('student_feedback')


def student_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Students.objects.get(admin=user)

    context={
        "user": user,
        "student": student
    }
    return render(request, 'student_template/student_profile.html', context)


def student_profile_update(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('student_profile')
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

            student = Students.objects.get(admin=customuser.id)
            student.address = address
            student.save()
            
            messages.success(request, "Profile Updated Successfully")
            return redirect('student_profile')
        except:
            messages.error(request, "Failed to Update Profile")
            return redirect('student_profile')


def student_view_result(request):
    student = Students.objects.get(admin=request.user.id)
    student_result = StudentResult.objects.filter(student_id=student.id)
    context = {
        "student_result": student_result,
    }
    return render(request, "student_template/student_view_result.html", context)





