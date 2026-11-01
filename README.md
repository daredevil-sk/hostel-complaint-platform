# Hostel Grievance & Accountability Platform
### IIT Patna | Student Welfare & Campus Management

> *"One complaint gets ignored. A hundred can't be."*

A transparent, accountable, community-driven web platform designed to streamline hostel grievances across IIT Patna. Built with a high-performance **FastAPI** backend and a responsive **React (Tailwind CSS)** dark-mode frontend.

---

## Table of Contents

1. [What the Platform Does](#what-the-platform-does)
2. [Key Features & Capabilities](#key-features--capabilities)
   - [Student Experience](#1-student-experience)
   - [Caretaker Accountability](#2-caretaker-accountability)
   - [Administrative Control](#3-administrative-control)
   - [Analytics & SLA Reporting](#4-analytics--sla-reporting)
   - [UI/UX & Design](#5-uiux--design-highlights)
3. [Campus Hostel Layout](#campus-hostel-layout)
4. [Architecture & Technology Stack](#architecture--technology-stack)
5. [Quick Start & Local Setup](#quick-start--local-setup)
6. [Demo Accounts & Testing](#demo-accounts--testing)
7. [REST API Documentation](#rest-api-documentation)
8. [Cloud Deployment](#cloud-deployment)
   - [Render.com](#deploying-to-rendercom)
   - [Railway / Docker / VPS](#deploying-to-railway-docker-or-vps)
9. [Project Structure](#project-structure)

---

## What the Platform Does

Hostel grievances (plumbing failures, water outages, electrical hazards, hygiene issues) are often reported informally over scattered WhatsApp groups, emails, or physical registers. Consequently, issues get lost, students lack visibility into repair progress, and caretakers lack clear prioritization tools.

This platform centralizes the grievance lifecycle into a **single public ledger**:
- **Consolidation**: Eliminates duplicate complaints by pooling student support behind single issues.
- **Accountability**: Database-backed "Seen" badges track the exact minute a caretaker opens an issue.
- **Transparency**: Every status transition is logged in a public activity timeline.
- **Student Closure Verification**: Complaints are only marked closed when the submitting student confirms the fix or when officially resolved.

---

## Key Features & Capabilities

### 1. Student Experience

- **Grievance Submission with Photo Evidence**: Submit detailed complaints with category tagging, location breakdown (Hostel, Block, Floor, Room/Area), and photo attachments.
- **Anonymous Complaint Submission**: Students can toggle "Submit Anonymously" to protect their privacy on sensitive complaints; their name is hidden from public view while internal audit logs maintain authenticity.
- **Community Support (Upvoting)**: Students can upvote existing complaints to indicate shared problems. The database strictly enforces one vote per student per complaint to prevent spam.
- **Delete Complaint Capability**: Submitting students can delete their own complaint directly from their dashboard as long as it is still in `Submitted` status (before caretaker inspection).
- **Resolution Confirmation & Reopen Loop**: When a caretaker marks a complaint as "Resolved", the student can verify the repair by clicking **Confirm Resolved** or **Reopen** with a reason if the issue persists.
- **Discussion & Comments**: Students and staff can discuss complaints directly on the detail page.
- **Student Dashboard ("My Complaints")**:
  - **My Submissions**: Track your open and resolved issues.
  - **Complaints I Support**: Monitor issues you've upvoted.
  - **In-App Notifications**: Real-time alerts when caretakers see, acknowledge, or update your grievances.

### 2. Caretaker Accountability

- **Caretaker "Seen" Timestamp**: The moment a caretaker or administrator opens an assigned complaint, the system automatically writes an immutable `first_seen_at` timestamp.
- **Formal Acknowledgement**: Caretakers can submit formal acknowledgements with custom work notes and an estimated completion date (ETA).
- **Lifecycle Status Workflow**: Strict state machine prevents arbitrary status changes:
  $$\text{Submitted} \longrightarrow \text{Acknowledged} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \longrightarrow \text{Closed}$$
- **Proof of Resolution**: Caretakers can upload photo evidence showing the completed repair before resolving an issue.
- **Caretaker Dashboard**:
  - Live metric counters for **Assigned**, **New/Unseen**, **Acknowledged**, **In Progress**, and **Overdue (>3 days)**.
  - Tabbed triage views (`Unseen`, `Assigned`, `In Progress`, `All`).
  - Inline action buttons to mark seen, acknowledge, or transition status.

### 3. Administrative Control

- **Admin Overview**: High-level platform statistics (total complaints, unassigned complaints, unread grievances, active users).
- **Complaint Assignment Engine**: Route grievances to specific caretakers or maintenance departments.
- **Duplicate Merging**: Merge duplicate grievances into a surviving complaint. Upvotes are consolidated without double-counting, and audit records preserve history.
- **User Management**: View registered students and staff; provision new caretaker or administrator accounts.
- **Audit Logging**: Comprehensive, queryable audit trail tracking all privileged operations with actor identity, action type, and timestamps.
- **Content Moderation**: Administrators can moderate inappropriate discussion comments.

### 4. Analytics & SLA Reporting

- **SLA Performance Metrics**:
  - Average time to first inspection (Hours to Seen).
  - Average time to acknowledgement (Hours to Ack).
  - Average time to resolution (Hours to Resolved).
- **Categorical & Hostel Breakdown**: Distribution of complaints across hostels and problem categories.
- **Top Supported Issues**: Live ranking of grievances with the highest community backing.
- **One-Click CSV Export**: Download a full CSV export of all complaint data for administrative reporting.

### 5. UI/UX & Design Highlights

- **Dark Mode by Default**: Tailored `#0F172A` / `#1E293B` slate-navy palette with indigo accents for reduced eye strain.
- **Mobile First & Auto-Closing Drawer**: Responsive navigation drawer that automatically collapses when a link is tapped on mobile devices.
- **Indian Standard Time (IST)**: All timestamps display in Indian Standard Time (`DD Mon YYYY, HH:MM AM/PM IST`).
- **Direct Navigation Buttons**: Every workflow ends with a direct action button (e.g. "View on Complaint Board" immediately redirects to the board).
- **Browser History Integration**: Hash routing (`#/`, `#/board`, `#/complaint/:id`, `#/submit`) enables native browser Back and Forward button navigation without page reloads.
- **1-Click Demo Logins**: Test any user role without typing credentials.
- **Clean Aesthetic**: Modern SVG icons, clean typography, and zero distracting emojis.

---

## Campus Hostel Layout

The system mirrors the actual residential layout of IIT Patna:

| Hostel Name | Resident Population | Notes |
|---|---|---|
| **Asima** | Girls | All blocks |
| **Aryabhatta** | Mixed | **Block C**: Girls &bull; **Blocks A, B, D**: Boys |
| **Kalam** | Boys | Blocks A, B, C, D |
| **CV Raman** | Boys | All blocks |

---

## Architecture & Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                   Browser Client (React SPA)                │
│  - Tailwind CSS Dark Theme                                  │
│  - Hash Router (#/board, #/complaint/:id, #/submit)         │
│  - Token-based Session Management                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Server                   │
│  - REST API Endpoints (/api/auth, /api/complaints, etc.)    │
│  - Static SPA & Media File Serving (/static, /uploads)      │
│  - Interactive Swagger Docs (/docs)                         │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLAlchemy 2.0 ORM
┌──────────────────────────────▼──────────────────────────────┐
│                      Database Layer                         │
│  - SQLite (Default local development)                       │
│  - PostgreSQL / Supabase / Neon (Production ready)          │
└─────────────────────────────────────────────────────────────┘
```

- **Backend**: Python 3.12, FastAPI 0.128, Uvicorn ASGI, Pydantic v2.
- **Database & ORM**: SQLAlchemy 2.0 with connection pooling, Alembic migration structure, support for SQLite and PostgreSQL (`psycopg3`/`psycopg2`).
- **Security**: Password hashing via `bcrypt` with salt rounds, Bearer token session authentication.
- **Frontend**: React 18, Tailwind CSS, Lucide-style vector SVG iconography.
- **Alternative UI**: Streamlit 1.40 fallback available via `streamlit run app.py`.

---

## Quick Start & Local Setup

### 1. Clone & Navigate to the Repository
```bash
git clone https://github.com/daredevil-sk/hostel-complaint-platform.git
cd hostel-complaint-platform
```

### 2. Create a Virtual Environment & Install Dependencies
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Initialize & Seed Demo Data
```bash
python seed.py
```
*(Use `python seed.py --reset` to wipe and re-seed the database).*

### 4. Start the Application

#### Standard Option: FastAPI + React SPA (Recommended)
```bash
python run_server.py
```
- Open your browser to **`http://localhost:8000`**
- Swagger API documentation is available at **`http://localhost:8000/docs`**

#### Alternative Option: Streamlit Dashboard
```bash
streamlit run app.py
```
- Open your browser to **`http://localhost:8501`**

---

## Demo Accounts & Testing

For fast grading, presentation, and development testing, the following pre-configured accounts are seeded:

| Role | Hostel | Email | Password |
|---|---|---|---|
| **Student (Girls)** | Asima | `student1@demo.teamr` | `demo1234` |
| **Student (Girls)** | Aryabhatta C | `student2@demo.teamr` | `demo1234` |
| **Student (Boys)** | Kalam | `student3@demo.teamr` | `demo1234` |
| **Student (Boys)** | CV Raman | `student4@demo.teamr` | `demo1234` |
| **Caretaker** | Campus Staff | `caretaker@demo.teamr` | `demo1234` |
| **Administrator** | Management | `admin@demo.teamr` | `demo1234` |

> *On the web sign-in page, click any of the 1-click login buttons to authenticate instantly without typing.*

---

## REST API Documentation

The FastAPI backend exposes standard OpenAPI/Swagger documentation at `/docs`. Below is a summary of primary endpoints:

### Authentication (`/api/auth`)
- `POST /api/auth/login` — Sign in with email and password.
- `POST /api/auth/register` — Create a new student account.
- `GET /api/auth/me` — Retrieve the currently authenticated profile.
- `POST /api/auth/logout` — Invalidate the active session token.
- `GET /api/auth/demo-accounts` — List pre-configured demo credentials.

### Complaints (`/api/complaints`)
- `GET /api/complaints` — Query complaints with filters (`search`, `category`, `hostel`, `status`, `priority`, `sort_by`, `page`, `page_size`).
- `POST /api/complaints` — Submit a new grievance (supports multipart photos and `is_anonymous`).
- `GET /api/complaints/{id}` — Retrieve full complaint details, timeline, comments, and seen status.
- `DELETE /api/complaints/{id}` — Delete a complaint (student submitter on `Submitted` status, or admin).
- `POST /api/complaints/{id}/vote` — Toggle student support (upvote/unvote).
- `POST /api/complaints/{id}/comments` — Post a discussion comment or official update.
- `POST /api/complaints/{id}/seen` — Caretaker explicitly marks complaint as seen.
- `POST /api/complaints/{id}/acknowledge` — Caretaker acknowledges grievance with notes & ETA.
- `POST /api/complaints/{id}/status` — Transition complaint status through allowed states.
- `POST /api/complaints/{id}/confirm-resolved` — Submitting student confirms successful resolution.
- `POST /api/complaints/{id}/upload-photo` — Upload resolution evidence photos.

### Dashboards & Management
- `GET /api/my-complaints` — Personal submissions and supported complaints for students.
- `GET /api/notifications` — Retrieve in-app notifications.
- `POST /api/notifications/read-all` — Mark all notifications as read.
- `GET /api/caretaker/dashboard` — Caretaker metrics and triage lists.
- `GET /api/admin/overview` — Administrative KPI overview.
- `POST /api/admin/assign` — Assign complaint to a caretaker or department.
- `POST /api/admin/merge` — Merge duplicate complaints.
- `GET /api/admin/audit-logs` — Audit log of administrative actions.
- `GET /api/analytics` — Live SLA and categorical analytics.
- `GET /api/analytics/export` — Stream dynamic CSV export of complaints.

---

## Cloud Deployment

Because the FastAPI server directly hosts the React SPA from the `/frontend` directory, **you do not need a separate Vercel frontend deployment**. The entire app runs as a single unified service.

### Deploying to Render.com

1. Create a free account at **[render.com](https://render.com)**.
2. Click **New +** &rarr; **Web Service** and connect your GitHub repository.
3. Configure the service settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**.

### Deploying to Railway, Docker, or VPS

- **Railway.app**: Connect the repository; Railway automatically detects the included [`Procfile`](Procfile) and starts Uvicorn.
- **Docker**: Build and run with:
  ```bash
  docker build -t hostel-app .
  docker run -p 8000:8000 hostel-app
  ```
- **PostgreSQL Database**: Set the `DATABASE_URL` environment variable:
  ```env
  DATABASE_URL=postgresql://user:password@host:5432/dbname
  ```
  The app automatically switches from SQLite to PostgreSQL with connection pooling.

---

## Project Structure

```
hostel_complaint_app/
│
├── backend/                  # FastAPI REST Backend
│   └── app.py                # API routes, auth dependencies, static SPA mounting
│
├── frontend/                 # React Single-Page Application
│   ├── index.html            # Dark-theme HTML host & Tailwind CSS configuration
│   └── app.jsx               # React component tree, routing, state, and UI views
│
├── src/                      # Shared Business Logic & Database
│   ├── db/
│   │   ├── database.py       # Engine creation, SQLite/PostgreSQL connectors, migrations
│   │   └── models.py         # SQLAlchemy ORM models (Complaints, Users, Votes, Comments, etc.)
│   ├── utils/
│   │   ├── auth.py           # Password hashing & verification
│   │   ├── complaints.py     # Complaint CRUD, state machine, SLA calculators, notifications
│   │   └── env_loader.py     # Environment variable loader
│   ├── components/
│   │   └── ui.py             # Shared UI helpers & Streamlit components
│   └── pages/                # Streamlit UI page views (legacy / fallback)
│
├── tests/                    # Test Suite
│   ├── test_fastapi_endpoints.py  # 16-point end-to-end integration test suite
│   ├── test_auth.py          # Authentication unit tests
│   ├── test_complaints.py    # Complaint lifecycle tests
│   ├── test_votes.py         # Voting constraint tests
│   └── test_merge.py         # Duplicate merge tests
│
├── uploads/                  # Local directory for photo evidence storage
├── Procfile                  # Cloud deployment runner (Render, Railway, Heroku)
├── run_server.py             # Local one-command development runner
├── seed.py                   # Demo data generator
└── requirements.txt          # Python dependency specifications
```

---

## License & Credits

Developed for the **IIT Patna Hostel Community**. Built with modern open-source technologies: FastAPI, React, SQLAlchemy, and Tailwind CSS.
