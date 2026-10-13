# 🎓 EduSphere — Smart Academic Management System

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**EduSphere** is an institutional-grade, developer-crafted academic management platform engineered for **IIMT UNIVERSITY**. It combines a restrained, high-density dark interface (`#090D16` midnight canvas, `#0F172A` cards, `#1E293B` dividers, `#2563EB` blue accents) with robust Django backend architecture.

The platform provides passwordless **cryptographic OTP authentication**, **Real Mailbox Delivery (Gmail SMTP)**, role-based dashboards (`STUDENT`, `TEACHER / FACULTY`, `ADMIN`), course management, batch attendance roll-call with 75% statutory compliance tracking, assignment submissions & grading, study material distribution, and a comprehensive privacy & compliance suite (GDPR / FERPA / COPPA).

---

## 🌟 Core Architecture & Features

### 🔐 1. Unified Passwordless Email OTP Authentication
- **Zero-Password Security**: Institutional sign-in requires no passwords. Users authenticate via a cryptographically random 6-digit one-time code sent directly to their email.
- **PBKDF2/SHA256 Hashing**: OTPs are salted and hashed before database storage—raw OTPs are never exposed in database records, API payloads, or logs.
- **Flood & Brute-Force Defenses**:
  - 5-minute strict OTP expiration.
  - 60-second cooldown timer between resend attempts.
  - Automatic challenge lockout after 5 incorrect attempts.
  - Multi-tier hourly rate limits per email address and IP.
  - Segmented 6-digit input with automated focus advance and clipboard paste handling.

### 📬 2. Real Mailbox Delivery (Gmail SMTP)
- Production-ready SMTP delivery configured via Google SMTP (`smtp.gmail.com:587` with STARTTLS).
- Dynamic `From` header alignment prevents provider-level `553 Sender mismatch` rejections.
- CLI Testing & Setup Utilities:
  - `python manage.py setup_gmail` — Interactive wizard to configure and verify Gmail SMTP.
  - `python manage.py send_test_email <recipient>` — Instant verification delivery to any real mailbox.
- Local dev console fallback with developer console banners when SMTP is unconfigured.

### 👥 3. Role-Based Access Control (RBAC) & Dashboards
- **Student Dashboard** (`/dashboard/student/`): Real-time course rosters, attendance progress rings, upcoming assignment deadlines, and evaluated grade cards.
- **Faculty Dashboard** (`/dashboard/teacher/`): Enrolled student rosters, 1-click batch attendance (*Mark All Present* / *Mark All Absent*), assignment publisher, submission evaluation queues, and study material distributor.
- **Admin Command Center** (`/dashboard/admin/`): University analytics, department distribution charts, user directory management, and audit logs.
- Role Management CLI:
  - `python manage.py set_role <email> <student|teacher|admin>` — Easily adjust any user's role.
  - `python manage.py create_faculty <email> --first-name "..." --last-name "..."` — Provision new faculty accounts.

### ⚖️ 4. Legal, Privacy & Compliance Suite
- Dedicated policy pages: Terms of Service, Privacy Policy, Cookie Policy, Tuition Refund Policy, Parental Consent (COPPA), and WCAG 2.1 AA Accessibility Statement.
- Granular Cookie Consent banner with customizable preferences (`Essential`, `Functional`, `Analytics`).
- GDPR Data Rights portal: Instant JSON data export archive and Right to Erasure / account deletion request filing.
- RFC 8058 1-click email unsubscribe headers.

---

## 🛠️ Technology Stack

- **Backend**: Django 6.1 (Python 3.12 / 3.14)
- **Production Server**: Gunicorn WSGI
- **Static Assets**: WhiteNoise `CompressedStaticFilesStorage`
- **Database**: PostgreSQL (Production) / SQLite (Zero-config local development)
- **Frontend**: Tailwind CSS, Inter Typography, Vanilla JavaScript, Chart.js

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Set Up Virtual Environment
```powershell
git clone https://github.com/<your-username>/edusphere.git
cd edusphere

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template and edit your `.env`:
```powershell
copy .env.example .env
```

### 3. Run Migrations & Seed Initial Data
```powershell
python manage.py migrate
python manage.py seed_data
```

### 4. Start Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

---

## 🐙 Publishing to GitHub

```bash
# 1. Ensure you are on the main branch
git branch -M main

# 2. Add your GitHub repository remote
# (Replace <your-username> and <repository-name> with your GitHub details)
git remote add origin https://github.com/<your-username>/edusphere.git

# 3. Push to GitHub
git push -u origin main
```

---

## 📦 Production Deployment Guide

### Option 1: Render (Recommended Blueprint)
1. Fork or push this repository to GitHub.
2. In Render, select **New +** > **Blueprint**.
3. Choose your repository. Render reads [`render.yaml`](render.yaml) and provisions:
   - Python Web Service running Gunicorn
   - Managed PostgreSQL Database
   - Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Click **Apply** to deploy.

### Option 2: Docker & Docker Compose
```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data
```

---

## 🧪 Verification & Automated Testing

Run the 21-scenario test suite verifying RBAC, OTP cryptographic lifecycle, and legal compliance:
```powershell
python manage.py test
```

---

## 📄 License & Institutional Accreditation

Licensed under the [MIT License](LICENSE).  
Official platform for **IIMT UNIVERSITY**, Meerut, Uttar Pradesh, India.
