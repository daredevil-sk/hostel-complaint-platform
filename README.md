# Team R — Hostel Grievance & Accountability Platform
## IIT Patna | Entrepreneurship & Innovation Project

> **"One complaint gets ignored. A hundred can't be."**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Demo Accounts & Seed Data](#demo-accounts--seed-data)
8. [User Roles & Permissions](#user-roles--permissions)
9. [Feature Checklist](#feature-checklist)
10. [Architecture](#architecture)
11. [Testing](#testing)
12. [Deployment](#deployment)
13. [Business Metrics](#business-metrics)
14. [Demo Script](#demo-script)
15. [Troubleshooting](#troubleshooting)

---

## Project Overview

Team R is a web application that centralizes hostel grievances at IIT Patna. Students submit complaints with photos and location details, and other students can add community support. Caretakers and administrators track progress through a transparent lifecycle — **Submitted → Seen → Acknowledged → Assigned → In Progress → Resolved**.

The key innovation is the **Caretaker "Seen" Indicator** — a database-backed record of exactly when a caretaker first opened a complaint. Students can distinguish between a complaint that has been submitted and one that has been actively received.

---

## Quick Start

```bash
# 1. Clone / enter the project directory
cd hostel_complaint_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env   # edit values if needed (SQLite works with defaults)

# 4. Seed demo data
python seed.py

# 5. Run the application
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## Installation

### Requirements

- Python 3.10 or later
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `streamlit` — web application framework
- `sqlalchemy` — database ORM
- `bcrypt` — password hashing
- `pandas` — data analysis
- `plotly` — charts
- `python-dotenv` — environment variable loading
- `faker` — optional test data generation
- `pytest` — test runner

---

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Key environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./hostel_complaints.db` | SQLAlchemy connection string |
| `APP_SECRET_KEY` | (set in .env) | Secret key — change in production |
| `UPLOAD_DIR` | `uploads` | Local directory for photo uploads |
| `MAX_UPLOAD_SIZE_MB` | `5` | Maximum upload size |
| `DEMO_MODE` | `true` | Show demo banner |

### Using PostgreSQL / Supabase

Change `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

For Supabase:
```
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

No other code changes are needed — the schema is PostgreSQL-compatible.

---

## Database Setup

### SQLite (default — no setup required)

The database file `hostel_complaints.db` is created automatically when the application starts.

### PostgreSQL

1. Create a database.
2. Set `DATABASE_URL` in `.env`.
3. Run `streamlit run app.py` — tables are created automatically.

### Reset and re-seed

```bash
python seed.py --reset   # drops all tables, re-creates, seeds demo data
```

---

## Running the Application

```bash
streamlit run app.py
```

Default URL: **http://localhost:8501**

---

## Demo Accounts & Seed Data

Run `python seed.py` to create demo accounts and fictional complaints.

> ⚠️ **All demo accounts and complaints are entirely fictional.**
> These do not represent real IIT Patna students or staff.

| Role | Email | Password |
|------|-------|----------|
| Administrator | admin@demo.teamr | demo1234 |
| Caretaker | caretaker@demo.teamr | demo1234 |
| Student 1 | student1@demo.teamr | demo1234 |
| Student 2 | student2@demo.teamr | demo1234 |
| Student 3 | student3@demo.teamr | demo1234 |

### Demo complaints

| ID | Title | Status |
|----|-------|--------|
| TR-2026-0001 | Water cooler not working — Block B | Resolved |
| TR-2026-0002 | No water in 2nd floor washrooms | In Progress |
| TR-2026-0003 | Broken door hinge — Room 312 | Acknowledged |
| TR-2026-0004 | Wi-Fi disconnecting in Block D | Submitted |
| TR-2026-0005 | Overflowing dustbins near mess | Assigned |
| TR-2026-0006 | Flickering corridor lights | Submitted |

---

## User Roles & Permissions

### Student
- Submit complaints
- View all public complaints
- Add/remove support (vote) — one vote per complaint
- Comment on complaints
- View their own submissions
- Reopen resolved complaints
- Confirm resolution

Students **cannot**: mark complaints as seen, acknowledge, assign, or change status.

### Caretaker
- View assigned complaints
- Mark complaints as seen (sets `first_seen_at` timestamp)
- Acknowledge complaints (separate from seen)
- Add work notes and estimated completion dates
- Update status: Acknowledged → Assigned → In Progress → Resolved
- Upload resolution photos
- Post official progress updates

Caretakers **cannot**: vote, impersonate other users, or modify student votes.

### Administrator
- All caretaker permissions
- Assign complaints to caretakers
- Change priority and visibility
- Merge duplicate complaints
- Moderate comments
- Manage user accounts
- View analytics and audit log
- Export data as CSV

### Authorization model

All privileged operations validate the caller's role server-side before executing any database change. Role values are read from the authenticated session — they are never accepted from client input.

---

## Feature Checklist

### ✅ Complete

- [x] Complaint submission with validation and unique ID generation (`TR-YYYY-NNNN`)
- [x] Public complaint board with search, filters, sorting, pagination
- [x] Voting system with database-enforced uniqueness (one vote per student per complaint)
- [x] Vote toggle (add / remove support)
- [x] Caretaker Seen indicator — `first_seen_at` recorded and immutable
- [x] Seen ≠ Acknowledged (two separate database fields and UI states)
- [x] Complaint lifecycle: Submitted → Acknowledged → Assigned → In Progress → Resolved → Reopened
- [x] Status transition validation (forbidden transitions rejected)
- [x] Role-based authorization on all privileged operations
- [x] Student dashboard (my complaints, supported complaints, notifications)
- [x] Caretaker dashboard (unseen, assigned, in-progress tabs, inline actions)
- [x] Administrator dashboard (overview, all complaints, assignments, merges, users, audit)
- [x] Analytics page (charts from real database records)
- [x] Complaint detail page with full timeline and comment thread
- [x] Comment system with official vs student distinction
- [x] Comment moderation
- [x] Photo upload (complaint and resolution evidence)
- [x] Duplicate complaint merging (votes transferred without double-counting)
- [x] In-app notifications
- [x] Audit log for privileged actions
- [x] CSV export
- [x] Seed data script with `--reset` option
- [x] Comprehensive test suite (34+ tests)
- [x] `.env.example` with documented variables
- [x] SQLite by default; PostgreSQL-compatible schema

### ⚠️ Partial / Documented Limitations

- [x] Caretaker "unauthorized scope" enforcement: Currently any caretaker can mark any complaint as seen. For a production deployment, add explicit scope checks based on assignment records.
- [x] Email notifications: Interface present; actual email delivery requires SMTP credentials in `.env` (not configured in demo).
- [x] Supabase Storage: Local filesystem storage is used by default. Supabase Storage can be integrated by updating `save_attachment()` in `src/utils/complaints.py`.
- [x] Supabase Auth: Custom bcrypt-based auth is used. Supabase Auth integration can replace this by updating `src/utils/auth.py`.

### ❌ Not Implemented

- [ ] Automated escalation reminders (email-based) — documented as requiring SMTP configuration
- [ ] AI-based priority suggestion — not claimed; manual priority assignment is used
- [ ] Supabase Row Level Security policies — applicable when migrating to Supabase backend

---

## Architecture

```
hostel_complaint_app/
├── app.py                      # Main entry point (streamlit run app.py)
├── seed.py                     # Demo data seeder
├── requirements.txt
├── .env.example
├── .env                        # (created from .env.example)
├── sample_export.csv           # Sample CSV export
│
├── src/
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM models (all 11 tables)
│   │   └── database.py         # Engine, session factory, init_db()
│   │
│   ├── utils/
│   │   ├── auth.py             # Password hashing, session, login/logout, role checks
│   │   └── complaints.py       # All business logic: CRUD, voting, seen, status, merge
│   │
│   ├── components/
│   │   └── ui.py               # Reusable UI components: cards, badges, sidebar
│   │
│   └── pages/
│       ├── home.py             # Landing page
│       ├── auth.py             # Login & registration
│       ├── board.py            # Public complaint board
│       ├── submit.py           # Complaint submission form
│       ├── complaint_detail.py # Full complaint detail + timeline + comments
│       ├── my_complaints.py    # Student dashboard
│       ├── caretaker_dashboard.py  # Caretaker dashboard
│       ├── admin_dashboard.py  # Admin dashboard
│       └── analytics.py        # Analytics charts
│
├── tests/
│   ├── conftest.py             # In-memory SQLite fixtures
│   ├── test_complaints.py      # Complaint creation, validation, IDs
│   ├── test_votes.py           # Voting uniqueness and toggle
│   ├── test_seen_indicator.py  # All seen/acknowledged tests from spec §18
│   ├── test_status_transitions.py  # Lifecycle and role authorization
│   ├── test_merge.py           # Duplicate merging
│   ├── test_auth.py            # Authentication and authorization
│   └── test_analytics.py      # Analytics metric calculation
│
├── uploads/                    # Photo uploads (created automatically)
└── .streamlit/
    └── config.toml             # Theme and server settings
```

### Database tables

| Table | Purpose |
|---|---|
| `profiles` | User accounts with role |
| `complaints` | Core complaint records |
| `complaint_votes` | One vote per student per complaint (unique constraint) |
| `complaint_comments` | Student and official comments |
| `complaint_status_history` | Immutable log of every status change |
| `caretaker_acknowledgements` | Seen and acknowledged timestamps per caretaker |
| `complaint_attachments` | Photo file references |
| `complaint_assignments` | Admin assignments to caretakers |
| `notifications` | In-app notification queue |
| `audit_logs` | Privileged action audit trail |
| `complaint_merges` | Merge history |

---

## Testing

```bash
# Run all tests
cd hostel_complaint_app
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_seen_indicator.py -v
```

Tests use an in-memory SQLite database — no setup required.

---

## Deployment

### Local (development)

```bash
streamlit run app.py
```

### Production considerations

1. Set `DATABASE_URL` to a PostgreSQL connection string.
2. Set `APP_SECRET_KEY` to a long random string.
3. Set `DEMO_MODE=false`.
4. Use a reverse proxy (nginx) in front of Streamlit.
5. Configure SMTP variables for email notifications.
6. Use environment-specific `.env` files; never commit secrets.

### Streamlit Community Cloud (free hosting)

1. Push to a public GitHub repository.
2. Go to share.streamlit.io and connect your repo.
3. Set secrets in the Streamlit Cloud dashboard (equivalent to `.env`).

---

## Business Metrics

### Adoption rate

```
adoption_rate = (students_with_at_least_one_complaint / total_enrolled_students) × 100
```

Track monthly. Target: >20% in first semester.

### Acknowledgement rate

```
acknowledgement_rate = (complaints_acknowledged / total_complaints_submitted) × 100
```

Target: >80% acknowledged within 24 hours.

### Acknowledgement SLA

```
within_SLA = (complaints_acknowledged_within_24h / total_acknowledged) × 100
```

### Resolution rate

```
resolution_rate = (complaints_resolved / total_complaints_submitted) × 100
```

### Average resolution time

Computed only for resolved complaints. Unresolved complaints are excluded.

```
avg_resolution_time = mean(resolved_at - created_at) for all resolved complaints
```

### Reopen rate

```
reopen_rate = (reopened_complaints / resolved_complaints) × 100
```

High reopen rate indicates resolutions are not adequate.

### Community engagement

```
avg_supporters_per_complaint = total_votes / total_complaints
```

Higher engagement means complaints are consolidating rather than being submitted separately.

---

## Demo Script

### For the Entrepreneurship & Innovation presentation

**Preparation**: Run `python seed.py --reset` to start fresh. Open the app at http://localhost:8501.

---

**Step 1 — Student submits a complaint**

1. Sign in as `student1@demo.teamr` / `demo1234`
2. Click **Submit a Complaint**
3. Fill in:
   - Title: "Hot water pipe leaking in Block B washroom"
   - Category: Plumbing
   - Hostel: Ganga, Block B, 1st Floor
   - Description: "Pipe has been leaking since morning. Water pooling on floor."
4. Submit — note the generated complaint ID (e.g. TR-2026-0007)

**Step 2 — Second student supports the complaint**

1. Sign in as `student2@demo.teamr`
2. Browse the board — find the new complaint
3. Click **Add support** — count goes to 1

**Step 3 — The complaint appears on the public board with "Not yet seen"**

- Point out the red **Not yet seen** badge on the complaint card

**Step 4 — Caretaker opens and marks as seen**

1. Sign in as `caretaker@demo.teamr`
2. Open Caretaker Dashboard → Unseen tab
3. Click the complaint
4. Click **Mark as Seen**

**Step 5 — "Seen by caretaker" indicator appears for the student**

1. Sign back in as `student1@demo.teamr`
2. Open the complaint detail
3. Show the **Seen by caretaker** badge with the timestamp

**Step 6 — Caretaker acknowledges the complaint**

1. Sign in as `caretaker@demo.teamr`
2. Click **Acknowledge** → add work notes → confirm

**Step 7 — Admin assigns and updates priority**

1. Sign in as `admin@demo.teamr`
2. Admin Dashboard → Assignments tab
3. Assign to caretaker, set priority to High

**Step 8 — Status update: In Progress**

1. Sign in as caretaker
2. Update status to **In Progress** with a note

**Step 9 — Resolution and reopening**

1. Caretaker marks as **Resolved**
2. Student confirms or reopens with a reason
3. Show the full timeline on the complaint detail page

**Step 10 — Analytics**

1. Sign in as admin
2. Open Analytics
3. Show charts — all data comes from actual database records

---

## Troubleshooting

### "ModuleNotFoundError" on startup

Ensure you are running from the project root directory:
```bash
cd hostel_complaint_app
streamlit run app.py
```

### Database errors on first run

The database is created automatically. If it gets corrupted:
```bash
del hostel_complaints.db
python seed.py
```

### Upload directory errors

The `uploads/` directory is created automatically. If permissions are wrong:
```bash
mkdir uploads
```

### Photos not displaying

Photos are served from the local filesystem. Ensure `UPLOAD_DIR` in `.env` matches the directory where files were saved.

### Slow on first load

The first load initializes the database and imports all modules. Subsequent loads are faster due to Streamlit's caching.

### Tests failing with import errors

Run pytest from the project root:
```bash
cd hostel_complaint_app
pytest tests/ -v
```
