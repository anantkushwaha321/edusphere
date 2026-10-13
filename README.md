# 🎓 IIMTMANIA — Premium College Community & Academic Platform

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**IIMTMANIA** is an institutional-grade, dark **Liquid Glass** college community and academic management platform built for **IIMT UNIVERSITY**. It merges a futuristic, high-contrast dark visual system (`#070A13` midnight navy, translucent glass surfaces, luminous borders, electric blue `#3B82F6` and violet `#8B5CF6` accents) with robust Django architecture.

The platform provides passwordless **cryptographic OTP authentication**, role-based liquid dashboards (`STUDENT`, `TEACHER`, `ADMIN`), student verification, course gradebooks, interactive attendance recording with statutory 75% compliance alerts, real-time assignment submissions, and a complete privacy & legal compliance portal (GDPR / FERPA / COPPA).

---

## 🌟 Key Features & Design System

### 🌌 1. Dark Liquid Glass UI/UX Design System
- **Color Architecture**: Deep midnight navy `#070A13`, secondary midnight `#0D1222`, luminous electric blue `#3B82F6`, cyber violet `#8B5CF6`, and neon cyan `#22D3EE`.
- **Liquid Glass Primitives**:
  - `.glass-panel`: Translucent backdrops (`rgba(13, 18, 34, 0.75)`) with restrained backdrop blur (`16px-24px`), subtle white border (`rgba(255, 255, 255, 0.1)`), and soft inner highlights.
  - `.glass-card` & `.spotlight-card`: Dynamic radial cursor-following spotlight glows (`pointermove` event listener with auto-fade).
  - `.glass-navbar` & `.glass-input`: Translucent glass forms, segmented numeric OTP boxes with neon focus rings.
  - `.badge-glass`: Translucent colored pills (`badge-glass-blue`, `badge-glass-violet`, `badge-glass-emerald`, `badge-glass-rose`, `badge-glass-amber`).
- **Interactive Background Engine**:
  - Ambient drifting radial gradient lights.
  - Canvas-based interactive particle constellation that gently reacts to pointer proximity.
  - Automatic frame throttling via `requestAnimationFrame` and tab-visibility detection (`document.hidden`) to ensure 60 FPS performance and zero background CPU drain.
  - Full support for `prefers-reduced-motion: reduce`.

### 🔐 2. Passwordless OTP Authentication
- **Zero-Password Security**: Log in using only your verified email.
- **PBKDF2/SHA256 Hashing**: 6-digit OTPs are cryptographically hashed before database persistence; raw OTPs are never stored or logged in production.
- **Brute-Force & Flood Defense**:
  - 5-minute strict passcode expiration.
  - 60-second cooldown timer between resend requests.
  - Automatic challenge locking after 5 failed attempts.
  - Multi-tier IP and email rate limiting.
  - Segmented 6-box input with automated keyboard advance and paste extraction.

### 👥 3. Role-Specific Liquid Dashboards
- **Student Dashboard**: Live enrolled course cards, attendance compliance ring, upcoming assignment countdowns, recent evaluation remarks, and printable transcript reports.
- **Faculty Dashboard**: Assigned courses roster, batch attendance roll-call launcher (*Mark All Present* / *Mark All Absent*), pending submission evaluation queue, and study notes distributor.
- **Admin Command Center**: System-wide statistics, interactive dark-themed Chart.js department distribution analytics, user directory management, and tamper-evident audit logs.

### ⚖️ 4. Legal, Privacy & Compliance Suite
- Dedicated policy pages: Terms of Service, Privacy Policy, Cookie Policy, Tuition Refund Policy, Parental Consent (COPPA), and WCAG 2.1 AA Accessibility Statement.
- Granular Cookie Consent banner with customizable preferences (`Essential`, `Functional`, `Analytics`).
- GDPR Data Rights portal: Instant JSON data export archive and Right to Erasure / account deletion request filing.
- RFC 8058 1-click email unsubscribe headers.

---

## 🛠️ Technology Stack

- **Backend Framework**: Django 6.1 (Python 3.12 / 3.14)
- **Production Server**: Gunicorn WSGI
- **Static Asset Caching**: WhiteNoise `CompressedStaticFilesStorage`
- **Database Engine**: PostgreSQL (Production) / SQLite (Local zero-config dev)
- **Frontend**: Tailwind CSS CDN, Custom Vanilla JS (`animations.js`, `main.js`, `otp.js`), Chart.js
- **Containerization**: Docker, Docker Compose
- **Environment Management**: `python-dotenv`, `dj-database-url`

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Activate Environment
```powershell
# Clone the repository
git clone https://github.com/<your-username>/iimtmania.git
cd iimtmania

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On Linux/macOS
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Initialize Environment & Seed Data
```powershell
# Copy sample configuration
cp .env.example .env

# Run database migrations
python manage.py migrate

# Seed sample institutional users & courses
python manage.py seed_data
```

### 4. Compile Static Assets & Launch
```powershell
python manage.py collectstatic --noinput
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to experience **IIMTMANIA**!

---

## 🧪 Demo Institutional Accounts (1-Click Fill)

On the login page (`/login/`), convenient 1-click buttons auto-fill pre-seeded demo accounts:

| Role | Email Address | Access Level |
| :--- | :--- | :--- |
| **Administrator** | `admin@iimtindia.net` | Full Institutional Leadership & Console |
| **Faculty** | `alan.turing@iimtindia.net` | Course Management & Attendance Evaluation |
| **Student** | `student.alice@iimtindia.net` | Course Enrollment, Attendance & Tasks |

*In local development (`EMAIL_BACKEND = console`), the 6-digit OTP code prints directly in your running terminal!*

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
The repository includes a production multi-stage [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml):

```bash
# Launch application & PostgreSQL database
docker compose up -d --build

# Run migrations and seed data
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data
```
The application will be live at `http://localhost:8000`.

### Option 3: Heroku / Railway / VPS
The repository includes a production [`Procfile`](Procfile) containing:
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```
Automatic database resolution is handled via `dj-database-url` reading `DATABASE_URL`.

---

## 🐙 Publishing to GitHub

```bash
# 1. Stage all changes
git add .

# 2. Commit with descriptive message
git commit -m "feat: IIMTMANIA — Dark Liquid Glass UI/UX Transformation & Production Deployment Engine"

# 3. Ensure branch is main
git branch -M main

# 4. Link to your GitHub remote
# (Replace <your-username> with your GitHub username)
git remote add origin https://github.com/<your-username>/iimtmania.git

# 5. Push to GitHub
git push -u origin main
```

---

## 🧪 Verification & Automated Testing

Run the full 21-scenario test suite verifying RBAC, OTP cryptographic lifecycle, and legal compliance:

```powershell
python manage.py test
```

---

## 📄 License & Institutional Accreditation

Licensed under the [MIT License](LICENSE).  
Official platform for **IIMT UNIVERSITY**, Meerut, Uttar Pradesh, India.
