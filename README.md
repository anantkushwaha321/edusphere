# 🎓 IIMT UNIVERSITY — Smart Academic Management System

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**IIMT UNIVERSITY Smart Academic Management System (AMS)** is a production-ready, cloud-deployable academic platform designed to streamline operations between students, faculty members, and institutional administrators.

The platform includes **passwordless OTP-based email authentication**, dedicated role-based dashboards, course catalog management, online assignment workflows with automatic late detection, attendance tracking with mandatory 75% compliance alerts, printable academic marksheets & transcripts, and complete WCAG 2.1 AA legal & privacy compliance portals.

---

## 🌟 Key Features & Architecture

### 1. 🔐 Passwordless OTP Authentication
- **Secure Email Verification**: Authentication without passwords using 6-digit cryptographically secure one-time passcodes (`secrets` module).
- **PBKDF2/SHA256 Hashing**: OTPs are hashed using Django's password hasher before being stored; plain passcodes are never exposed in database records or API responses.
- **Defense Mechanisms**:
  - 5-minute strict passcode expiration.
  - 60-second resend cooldown timer.
  - Automatic challenge invalidation after 5 failed attempts.
  - Multi-tier rate limiting (max 5 requests/hr per email, max 15 requests/hr per IP).
  - Role isolation: Self-registration is strictly restricted to `STUDENT` profiles; elevated roles (`ADMIN`, `TEACHER`) can only be provisioned by administrators.

### 2. 👥 Role-Based Access Control (RBAC) & Portals
- **Student Portal**:
  - Live course enrollment status and credit hour tracking.
  - Upcoming assignment deadlines with submission status badges.
  - Real-time grade notifications with teacher remarks.
  - Attendance compliance meter with 75% mandatory threshold alerts.
  - Official student transcript & report card with print layout (`window.print()`).
- **Faculty Portal**:
  - Assigned course management and syllabus delivery.
  - Assignment creator with attachments, maximum marks, and due dates.
  - Grading studio with percentage and letter grade calculation (`A+`, `A`, `B`, `C`, `D`, `F`).
  - Interactive roll-call attendance launcher with *Mark All Present* / *Mark All Absent* toggles.
  - Gradebook matrix and 1-click CSV attendance/grade exports.
- **Administrator Portal**:
  - Institutional high-level metrics (Total Students, Faculty, Courses, Campus Attendance Rate).
  - Department enrollment distribution analytics (Chart.js).
  - User account lifecycle management (creation, profile review, activation/deactivation).
  - Comprehensive activity audit trail with client IP tracking.

### 3. ⚖️ Privacy, Legal & Regulatory Compliance (FERPA / GDPR / COPPA / CCPA)
- **Official Policy Frameworks**: Institutional Privacy Policy, Terms of Service, Cookie Policy, Tuition Refund Schedule (Zero Hidden Fees), and Accessibility Statement.
- **Cookie Consent Banner & Modal**: Granular consent preferences API (`Essential`, `Functional`, `Analytics`).
- **Data Rights Portal (DSAR)**: Instant JSON data export archive (GDPR Art. 20) and Right to Erasure / Account Deletion request filing (GDPR Art. 17).
- **COPPA Parental Consent**: Verifiable consent tracking for minor students (`< 18` and `< 13`).
- **RFC 8058 1-Click Email Unsubscribe**: Automatic `List-Unsubscribe` headers and preference management.

---

## 🛠️ Technology Stack

- **Backend Framework**: Django 6.1 (Python 3.12 / 3.14)
- **WSGI Production Server**: Gunicorn
- **Static Assets Engine**: WhiteNoise (Compressed & Cached)
- **Database**: PostgreSQL (Production) / SQLite (Zero-config local development)
- **Frontend & UI**: Tailwind CSS, FontAwesome/Heroicons SVGs, Chart.js
- **Media & File Storage**: Pillow, Django Media Storage
- **Environment Management**: `python-dotenv`, `dj-database-url`

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Set Up Virtual Environment
```powershell
# Clone the repository
git clone https://github.com/<your-username>/iimt-university-ams.git
cd iimt-university-ams

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On Linux/macOS
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(By default, `.env` runs with SQLite and the console email backend so OTP passcodes print directly to your terminal).*

### 4. Run Migrations & Seed Sample Data
```powershell
python manage.py migrate
python manage.py seed_data
```

### 5. Launch the Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Demo Login Accounts (1-Click Fill)

The login screen at `/login/` contains **1-Click Test Demo Account** buttons:

| Role | Email Address | Description |
| :--- | :--- | :--- |
| **Administrator** | `admin@iimtindia.net` | Institutional Administrator & Dean |
| **Teacher** | `alan.turing@iimtindia.net` | Dr. Alan Turing (Computer Science HOD) |
| **Student** | `student.alice@iimtindia.net` | Alice Smith (B.Tech CSE Student) |

*When running locally, click **Send Verification Code**, then view the 6-digit code printed in your server terminal output!*

---

## 📦 Production Deployment Guide

The codebase is 100% cloud-ready with zero additional configuration needed.

### Option 1: Deploy on Render (Recommended)
1. Fork or push this repository to your GitHub account.
2. In the Render Dashboard, click **New +** > **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](render.yaml) and provision:
   - Web Service with Python & Gunicorn
   - Managed PostgreSQL Database
   - Auto-migration build commands
   - Environment variables
4. Click **Apply** to deploy!

### Option 2: Deploy with Docker & Docker Compose
The project includes a multi-stage production [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml) configured with PostgreSQL:

```bash
# Build and launch containers
docker compose up -d --build

# Run initial migrations and seed demo data
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data
```
The application will be live at `http://localhost:8000`.

### Option 3: Deploy on Railway
1. Click **New Project** > **Deploy from GitHub repo**.
2. Add a **PostgreSQL** database service.
3. In the Web service settings, set the environment variables from `.env.example` (Railway automatically provides `DATABASE_URL`).
4. Railway will automatically detect the [`Procfile`](Procfile) and launch Gunicorn.

---

## 🐙 How to Publish on GitHub

Follow these steps to publish this repository to your GitHub account:

```bash
# 1. Initialize git repository (if not already initialized)
git init

# 2. Add all files
git add .

# 3. Commit changes
git commit -m "feat: Initial release of IIMT UNIVERSITY Academic Management System"

# 4. Set the main branch
git branch -M main

# 5. Link your GitHub remote repository
# Replace <your-username> with your GitHub username
git remote add origin https://github.com/<your-username>/iimt-university-ams.git

# 6. Push to GitHub
git push -u origin main
```

---

## 🧪 Running Automated Tests

Run the comprehensive 21-scenario test suite verifying RBAC, OTP authentication, rate limiting, and regulatory compliance:

```powershell
# Run the entire test suite
python manage.py test

# Run only the OTP authentication tests
python manage.py test accounts

# Run only the compliance & legal tests
python manage.py test compliance
```

---

## 📄 License & Attribution

This project is open-source software licensed under the [MIT License](LICENSE).  
Developed for **IIMT UNIVERSITY** — *Transforming Education, Empowering Minds*.
