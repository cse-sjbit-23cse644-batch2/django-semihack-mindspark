
Django-semihack-starter
Starter template for semi-hackathon

🚀 Django Semi-Hackathon: MindSpark

📋 Project Details
Theme: Dynamic syllabus authoring & pdf generator
Team Members: Sumit Anand (1JB23CS164), Alankrit Gupta (1JB23CS017), Saket Raj (1JB23CS133), Birajdar Omkar Dayanand (1JB23CS027)
Live URL: [To be filled after deployment]

✅ Submission Checklist
Code runs with pip install -r requirements.txt
DEBUG=False in production settings
Working AJAX endpoint (tested live)
CSV/PDF export functional
CO-SDG mapping table completed below
150-word SDG justification included

🎯 CO-SDG Mapping Table
Course Outcome | How This Project Demonstrates It | SDG Target Addressed
CO1: MVT Architecture | URL routing for create/preview/PDF endpoints | SDG 4.3
CO2: Models & Forms | Syllabus/Module models + dynamic formsets | SDG 4.7
CO3: Template Reuse | Reusable base.html + HTML/PDF template sharing CSS | SDG 4.A
CO4: PDF Generation | WeasyPrint PDF with CSS paged media | SDG 9.5
CO5: Dynamic Form UX | Dynamic formset row add/remove via AJAX | SDG 9.C

📝 150-word SDG Justification
Our project delivers an end-to-end syllabus authoring and publishing workflow that directly supports SDG 4 (quality education) and SDG 9 (innovation and infrastructure). By digitizing course outcomes, modules, and assessments with structured models and guided forms, we improve curriculum consistency and ease of updates, supporting SDG 4.3 and 4.7 through better planning of inclusive, outcome-based learning. The reusable templates and PDF generation create accessible learning resources for students and stakeholders (SDG 4.A), while the approval workflow increases accountability and academic quality. The system uses MVT architecture, dynamic formsets, and automated exports to strengthen institutional digital capability (SDG 9.5). Web-based access and streamlined data entry reduce manual effort and improve connectivity across staff and students, aligning with SDG 9.C by expanding the use of ICT tools in education. It also enables revisions and transparent reporting for audits.

📦 Setup Instructions
git clone https://github.com/cse-sjbit-23cse644-batch2/django-semihack-mindspark.git
cd django-semihack-mindspark
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

✅ Pre-Deploy Checklist
DEBUG = False in settings.py
STATIC_ROOT configured
ALLOWED_HOSTS includes cloud domain
gunicorn in requirements.txt
Local python manage.py collectstatic ran successfully

🚀 Deployment Guide (Free Tier: Render)
Follow these steps on Event Day to make your app publicly accessible for judging.

Sign Up & Connect
Go to render.com -> Sign up with GitHub
Authorize Render to access your repos

Create Web Service
Click New + -> Web Service -> Connect this repo
Fill in:
Name: team-xyz-app
Region: Oregon or Frankfurt (closest to India)
Branch: main
Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput
Start Command: gunicorn student_management_system.wsgi (replace with your actual Django folder if different)

Environment Variables (Critical)
Click Advanced -> Add Environment Variable:
SECRET_KEY = Generate at miniwebtool.com/django-secret-key-generator
DEBUG = False
ALLOWED_HOSTS = *.onrender.com, localhost, 127.0.0.1

Deploy & Verify
Click Create Web Service -> Wait 2-4 mins for build
Once live, copy the https://...onrender.com URL
Test: Open URL, check CSS/JS loads, test AJAX endpoint, download CSV/PDF
Update this README.md with your live URL

🚨 Troubleshooting Quick Fixes
Issue | Fix
Application Error | Ensure gunicorn is in requirements.txt & wsgi path matches your project folder
Broken CSS/JS | Add STATIC_ROOT = BASE_DIR / "staticfiles" to settings.py
DisallowedHost | Verify ALLOWED_HOSTS env var or settings.py matches your Render domain
DB locked/migrations fail | Free tier uses SQLite by default. It's fine for hackathon demos. No extra config needed.

💡 Note: After deployment, every git push to main auto-triggers a rebuild. No manual server restarts needed.
# Django-semihack-starter
Starter template for semi-hackathon
# 🚀 Django Semi-Hackathon: [Team Name]

## 📋 Project Details
- **Theme**: [e.g., TH-03: Elective Choice System]
- **Team Members**: @student1, @student2, @student3, @student4
- **Live URL**: [To be filled after deployment]

## ✅ Submission Checklist
- [ ] Code runs with `pip install -r requirements.txt`
- [ ] `DEBUG=False` in production settings
- [ ] Working AJAX endpoint (tested live)
- [ ] CSV/PDF export functional
- [ ] CO-SDG mapping table completed below
- [ ] 150-word SDG justification included

## 🎯 CO-SDG Mapping Table
| Course Outcome | How This Project Demonstrates It | SDG Target Addressed |
|---------------|----------------------------------|---------------------|
| CO1: MVT Architecture | [Brief explanation] | SDG 4.5 |
| CO2: Models & Forms | [Brief explanation] | SDG 9.5 |
| ... | ... | ... |

## 📦 Setup Instructions
```bash
git clone [your-repo-url]
cd [repo-name]
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
### ✅ Pre-Deploy Checklist
- [ ] `DEBUG = False` in `settings.py`
- [ ] `STATIC_ROOT` configured
- [ ] `ALLOWED_HOSTS` includes cloud domain
- [ ] `gunicorn` in `requirements.txt`
- [ ] Local `python manage.py collectstatic` ran successfully
## 🚀 Deployment Guide (Free Tier: Render)
*Follow these steps on Event Day to make your app publicly accessible for judging.*

1. **Sign Up & Connect**
   - Go to [render.com](https://render.com) → Sign up with GitHub
   - Authorize Render to access your repos

2. **Create Web Service**
   - Click `New +` → `Web Service` → Connect this repo
   - Fill in:
     - **Name**: `team-xyz-app`
     - **Region**: `Oregon` or `Frankfurt` (closest to India)
     - **Branch**: `main`
     - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
     - **Start Command**: `gunicorn project_name.wsgi` *(replace `project_name` with your actual Django folder)*

3. **Environment Variables (Critical)**
   Click `Advanced` → `Add Environment Variable`:
   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Generate at [miniwebtool.com/django-secret-key-generator](https://miniwebtool.com/django-secret-key-generator/) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `*.onrender.com, localhost, 127.0.0.1` |

4. **Deploy & Verify**
   - Click `Create Web Service` → Wait 2–4 mins for build
   - Once live, copy the `https://...onrender.com` URL
   - ✅ Test: Open URL, check CSS/JS loads, test AJAX endpoint, download CSV/PDF
   - 📝 Update this `README.md` with your live URL

### 🚨 Troubleshooting Quick Fixes
| Issue | Fix |
|-------|-----|
| `Application Error` | Ensure `gunicorn` is in `requirements.txt` & `wsgi` path matches your project folder |
| Broken CSS/JS | Add `STATIC_ROOT = BASE_DIR / "staticfiles"` to `settings.py` |
| `DisallowedHost` | Verify `ALLOWED_HOSTS` env var or `settings.py` matches your Render domain |
| DB locked/migrations fail | Free tier uses SQLite by default. It's fine for hackathon demos. No extra config needed. |

💡 **Note:** After deployment, every `git push` to `main` auto-triggers a rebuild. No manual server restarts needed.

