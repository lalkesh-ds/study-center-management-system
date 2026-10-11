# Smart Library & Study Center Management System

A backend-first management platform for study centers and reading rooms that lease a fixed set of physical desks to different students across non-overlapping daily shifts.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)

**Domain:** space-as-a-service / facility management · **Type:** REST API backend + Streamlit front-desk UI

---

## Overview

Study centers (common for students preparing for competitive exams) do not lend books. They rent desks. Because rent is fixed per square foot, the same physical desk is leased to different students on different shifts through the day. Managing this in registers or spreadsheets leads to double-booked desks, students holding two desks at once, expired students still being let in, and fee balances that drift across renewals.

This system models the facility as **100 desks (1–100)**, **4 canonical daily shifts**, and **date-ranged memberships**, and enforces booking invariants in the database itself rather than relying on application code or UI behavior.

**Designed for:** the owner and front-desk staff of a single-branch study center (roles: `ADMIN`, `STAFF`).

**What is technically interesting**

- Double-booking is prevented at the database level with PostgreSQL `btree_gist` exclusion constraints over `(seat, date range, minute range)`, backed by `SELECT ... FOR UPDATE` row locking in the admission service.
- Time-dependent statuses (`EXPIRING_SOON`, `EXPIRED`, `UPCOMING`) are **derived on read**, not stored, so there are no stale-state bugs from missed cron jobs.
- The financial model separates the billing obligation (`memberships.final_fee`) from an append-only payment ledger (`payments`), with voiding instead of deletion.

---

## Facility Model

Operating hours: **07:00–23:00, 7 days a week (16 hours/day)**.

| Shift | Time | Minutes from midnight `[start, end)` | Duration | Default fee |
| :-- | :-- | :-- | :-- | :-- |
| Morning | 07:00–11:00 | `[420, 660)` | 4 h | ₹800 |
| Afternoon | 11:00–15:00 | `[660, 900)` | 4 h | ₹800 |
| Evening | 15:00–23:00 | `[900, 1380)` | 8 h | ₹1,200 |
| Full Day | 07:00–23:00 | `[420, 1380)` | 16 h | ₹2,200 |

### Core invariants

1. **Half-open time intervals.** Shifts are `[start, end)`. Two shifts overlap iff `S1 < E2 AND S2 < E1`, so Morning and Afternoon touch at 11:00 without colliding.
2. **Inclusive calendar dates.** Memberships are `[start_date, end_date]`. Two ranges overlap iff `S1 <= E2 AND S2 <= E1`, so an Oct 1–31 membership and a Nov 1–30 renewal do not collide.
3. **Persisted vs derived status.** Only `ACTIVE` and `CANCELLED` are stored. `UPCOMING`, `EXPIRING_SOON` (within 3 days of `end_date`) and `EXPIRED` are computed on read.
4. **One student, one place at a time.** A student may hold several memberships on the same dates only if their time intervals are disjoint (e.g. Morning on seat 25 and Evening on seat 40).
5. **Full Day exclusivity.** A Full Day membership blocks Morning, Afternoon and Evening on that seat for its date range.
6. **Inactive seats** (`is_active = FALSE`, e.g. under maintenance) cannot receive new memberships.
7. **Student status is independent of membership status.** An expired student stays `ACTIVE` in the directory.

### Capacity metrics

Because 100 desks are time-shared, a single "occupancy" number is misleading. The analytics module reports three:

| Metric | Formula |
| :-- | :-- |
| Physical desk utilization | desks with an active booking today / 100 |
| Slot occupancy | slots consumed today / 300 (Full Day = 3 slots) |
| Seat-hour occupancy | seat-hours booked today / 1,600 |

---

## Architecture

Layered architecture with a strict separation between presentation and backend: the Streamlit UI talks to the backend **only over HTTP/JSON** and never imports SQLAlchemy, so it can be replaced (the spec names React as the future option) without backend changes.

```mermaid
flowchart TD
    UI["Streamlit front desk<br/>(frontend/streamlit_app)"] -->|"HTTP REST / JSON<br/>Bearer JWT"| API
    subgraph Backend["FastAPI application"]
        API["API layer<br/>routers, validation, exception mapping"] --> SVC["Service layer<br/>allocation, memberships, payments,<br/>attendance, analytics"]
        SVC --> REPO["Repository layer<br/>SQLAlchemy 2.0, row locking"]
    end
    REPO --> DB[("PostgreSQL 15+<br/>btree_gist exclusion constraints")]
```

| Layer | Responsibility |
| :-- | :-- |
| Presentation | Rendering, input, seat grid, Plotly charts. No business logic. |
| API (`api/v1/endpoints`) | Routing, status codes, Pydantic v2 schemas, dependency injection (DB session, auth). No raw SQL. |
| Services | Conflict detection, admission, status derivation, ledger reconciliation, renewals, cancellations. |
| Repositories | Query encapsulation, `with_for_update()` locks, commit/rollback boundaries. |
| PostgreSQL | ACID, foreign keys, GiST exclusion constraints, ledger storage. |

### Admission workflow

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Membership service
    participant D as PostgreSQL
    C->>S: POST /api/v1/memberships
    S->>D: BEGIN; SELECT seat FOR UPDATE
    S->>D: Validate seat active + load shift
    S->>D: Check seat conflict and student conflict
    S->>D: INSERT membership (fee = base - discount)
    S->>D: INSERT initial payment (optional, amount <= fee)
    D-->>S: COMMIT (GiST constraint is the final backstop)
    S-->>C: 201 Created, or 409 SEAT_ALREADY_BOOKED / STUDENT_TIME_COLLISION
```

---

## Tech Stack

| Layer | Technology |
| :-- | :-- |
| Language | Python 3.10+ |
| API framework | FastAPI (ASGI, served with Uvicorn) |
| Validation / schemas | Pydantic v2 |
| ORM | SQLAlchemy 2.0 (typed `Mapped` models) |
| Database | PostgreSQL 15+ with `btree_gist` |
| Migrations | Alembic |
| Auth | JWT bearer tokens, Argon2id password hashing |
| Frontend | Streamlit (multipage), Plotly charts |
| Testing | Pytest |

---

## Project Structure

```text
library-management-system/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # auth, students, seats, shifts, memberships,
│   │   │                       # payments, attendance, dashboard, reports
│   │   ├── core/               # config (env), security (JWT/hashing), exceptions, logging
│   │   ├── db/                 # engine/session, declarative base
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── repositories/       # data access layer
│   │   ├── services/           # business logic (allocation, membership, payment,
│   │   │                       #   attendance, analytics)
│   │   ├── utils/time_ranges.py
│   │   └── main.py             # FastAPI entrypoint
│   └── tests/
├── frontend/streamlit_app/     # app.py, api_client.py, components/, pages/
├── migrations/                 # Alembic
├── scripts/                    # seed_data.py, backup_db.sh, generate_pdf.py
├── docs/                       # MASTER_TECHNICAL_SPECIFICATION.md
├── .env.example
├── requirements.txt
└── README.md
```

<!-- VERIFY: structure above is taken from the architecture spec (section 10). Compare against the actual repository tree before publishing. -->

---

## Database

PostgreSQL 15+, normalized to 3NF, managed with Alembic migrations.

| Table | Purpose |
| :-- | :-- |
| `users` | Staff accounts with role `ADMIN` / `STAFF` |
| `students` | Directory: unique `student_code` and `mobile`, ID proof, status |
| `seats` | Desks 1–100, `is_active`, power outlet / locker flags |
| `shifts` | Four canonical shifts with minute bounds and base fee |
| `memberships` | Contracts: seat, shift, date range, fee breakdown, status, `renewed_from_id` lineage |
| `payments` | Ledger: unique receipt number (`RCP-YYYYMMDD-XXXX`), method, `COMPLETED` / `VOIDED` |
| `attendance` | Daily check-in / check-out, unique per `(membership_id, attendance_date)` |
| `audit_logs` | Audit trail for sensitive mutations (voids, cancellations) |

`v_memberships_expanded` is a view that joins students, seats and shifts and computes `derived_status`, `total_paid`, `due_amount` and `payment_status` (`PENDING` / `PARTIAL` / `PAID`).

### Key constraints

```sql
-- No two ACTIVE memberships may share a seat, a date range and a time range
CONSTRAINT exclude_seat_time_conflict EXCLUDE USING gist (
    seat_id WITH =,
    daterange(start_date, end_date, '[]') WITH &&,
    int4range(start_minute, end_minute, '[)') WITH &&
) WHERE (status = 'ACTIVE')
```

A second constraint, `exclude_student_time_conflict`, applies the same rule per `student_id`. Other checks include `final_fee = base_fee - discount_amount`, `start_date <= end_date`, and cancellation / void metadata that must be present exactly when the row is cancelled / voided.

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : authors
    STUDENTS ||--o{ MEMBERSHIPS : holds
    SEATS ||--o{ MEMBERSHIPS : hosts
    SHIFTS ||--o{ MEMBERSHIPS : templates
    MEMBERSHIPS ||--o{ PAYMENTS : "paid by"
    MEMBERSHIPS ||--o{ ATTENDANCE : "logged in"
    MEMBERSHIPS |o--o| MEMBERSHIPS : "renewed_from"
```

---

## API

The backend is a FastAPI app, so interactive OpenAPI docs are served at `/docs` (Swagger UI) and `/redoc` when it is running. All routes are under `/api/v1`. Authentication is a Bearer JWT; voiding payments is admin-only.

| Area | Method & path | Purpose |
| :-- | :-- | :-- |
| Auth | via `endpoints/auth.py` | Staff login and JWT issuance |
| Students | `POST /students`, `GET /students`, `GET/PATCH /students/{id}` | Register, search, view, update |
| Seats | `GET /seats`, `GET /seats/availability`, `PATCH /seats/{id}/status` | Inventory, availability matrix, maintenance toggle |
| Shifts | `GET /shifts` | List shift definitions |
| Memberships | `POST /memberships`, `GET /memberships`, `GET /memberships/{id}` | Admit and query |
| | `POST /memberships/{id}/renew`, `POST /memberships/{id}/cancel` | Renewal chain; cancellation with immediate seat release |
| Payments | `POST /payments`, `POST /payments/{id}/void`, `GET /memberships/{id}/payments` | Collect, void (ADMIN, within 24 h, reason required), list |
| Attendance | `POST /attendance/check-in`, `POST /attendance/{id}/checkout`, `GET /attendance/daily` | Front-desk attendance |
| Dashboard | `GET /dashboard/summary`, `GET /dashboard/occupancy-grid` | KPIs and seat grid |
| Reports | `GET /reports/expiring`, `GET /reports/revenue` | Expiry queue, revenue |
| Health | `GET /api/v1/health` | Health check |

<!-- VERIFY: The auth route path is not specified in the spec. The spec also mentions /reports/revenue/export and /reports/students/export (CSV) which are not in its endpoint tables. Confirm these exist before listing them. -->

Typical error codes: `SEAT_ALREADY_BOOKED` (409), `STUDENT_TIME_COLLISION` (409), `MOBILE_EXISTS` (409), `PAYMENT_EXCEEDS_DUE` (400), `CANNOT_RENEW_CANCELLED` (400), `ALREADY_CANCELLED` (400), `ADMIN_ONLY` (403), `NO_ACTIVE_MEMBERSHIP_TODAY` (400), `ALREADY_CHECKED_IN` (409).

---

## Frontend

A Streamlit multipage app that calls the backend through `api_client.py`.

| Page | Responsibility |
| :-- | :-- |
| Seat Grid | 10×10 floor plan of 100 desks, color-coded by shift occupancy; maintenance toggle |
| Students | Searchable directory, registration, profile history |
| Memberships | Admissions, renewals, cancellations |
| Cashier Payments | Installments, receipts, admin-only voiding |
| Attendance | Quick check-in / check-out, daily roster |
| Analytics Dashboard | Occupancy KPIs, expiring memberships, revenue by payment method |

---

## Authentication & Security

- Passwords hashed with **Argon2id**.
- Stateless **JWT** bearer tokens (HS256, 8-hour expiry).
- **Role-based access control** (`ADMIN`, `STAFF`) through FastAPI dependencies.
- Parameterized queries only, via the SQLAlchemy ORM.
- Payments are never deleted; voids require an admin, a reason, and happen within 24 hours.
- Sensitive mutations are written to `audit_logs`.

> **Security note:** keep `SECRET_KEY`, database credentials and any other secrets in `.env` or your deployment's secret store. Never commit them. Change the seeded admin password immediately after first run.

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 15+ (local or hosted) with permission to create the `btree_gist` extension
- Git

### 1. Clone and install

```bash
git clone <your-repository-url>
cd library-management-system
python -m venv .venv
```

Activate the environment:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

| Variable | Purpose |
| :-- | :-- |
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://user:password@host:5432/library_db` |
| `SECRET_KEY` | JWT signing key, at least 32 characters |

<!-- VERIFY: confirm the full variable list against .env.example and backend/app/core/config.py. -->

### 3. Migrate and seed

```bash
python -m alembic upgrade head
python scripts/seed_data.py      # 100 seats, 4 shifts, default admin user
```

### 4. Run

```bash
# 1. Backend (Terminal 1)
uvicorn backend.app.main:app --reload --port 8000

# 2. Premium React Frontend (Terminal 2 - Recommended)
cd frontend/react_app
npm run dev

# 3. Streamlit Front Desk UI (Terminal 3 - Optional Legacy)
streamlit run frontend/streamlit_app/app.py
```

| Service | URL | Notes |
| :-- | :-- | :-- |
| **React Web App** | http://localhost:5173 | Modern production web application (Vite + React 19 + Tailwind CSS) |
| **Streamlit UI** | http://localhost:8501 | Legacy front desk interface |
| **FastAPI Swagger** | http://localhost:8000/docs | Interactive API explorer & schema contracts |
| **FastAPI ReDoc** | http://localhost:8000/redoc | Formal REST documentation |
| **Health Check** | http://localhost:8000/api/v1/health | System readiness & database connectivity |

Default login credentials seeded by `scripts/seed_data.py`:
- **Admin**: `admin` / `Admin@123`
- **Staff / Operator**: `librarian` / `Staff@123`

---

## Testing

```bash
python -m pytest backend/tests/ -v
```

Tests are organized around the system's risk areas: allocation and boundary math (half-open handovers, Full Day blocking, concurrent bookings), membership lifecycle (admission, discounts, overpayment, renewal, cancellation), payments (installments, voiding rules), attendance, analytics, and auth / RBAC.

<!-- VERIFY: the previous README claimed "54 automated tests" and listed test files that differ from the spec (spec lists test_concurrency.py and test_api/). Run pytest, then state the real count and file list here. -->

---

## Operations

`scripts/backup_db.sh` takes a gzipped `pg_dump` and prunes backups older than 30 days. Edit its `BACKUP_DIR`, host, user and database name for your environment before scheduling it.

---

## Design Decisions

| Decision | Rationale |
| :-- | :-- |
| Derive `EXPIRING_SOON` / `EXPIRED` on read | Avoids stale states when a nightly job fails and avoids write amplification on historical rows |
| Half-open `[start, end)` shift intervals | Lets consecutive shifts hand over at the same minute without false conflicts |
| Inclusive calendar dates | Matches how subscriptions are sold (Oct 1–31) and makes renewals seamless |
| Row lock **plus** GiST exclusion constraint | The lock serializes staff actions; the constraint guarantees correctness even if application code has a bug |
| Separate fee contract from payment ledger | Supports partial payments and voids without losing accounting history |
| HTTP-only frontend boundary | Keeps the UI replaceable |

---

## Scope & Roadmap

**Known limitations of v1.0:** single facility; fixed canonical shifts only (no arbitrary hourly bookings); refunds on cancellation are handled manually outside the system; attendance is manual / web-kiosk (no biometric hardware sync).

**Planned (not implemented):** React / Next.js portal, Flutter student app, ZKTeco biometric integration, ML-based renewal-risk alerts and demand forecasting (requires collected operational data), multi-branch / multi-tenant support.

**Build phases** (from the specification):

| Phase | Scope |
| :-- | :-- |
| 01 | Architecture and specification |
| 02–04 | Database and migrations, FastAPI foundation, master repositories |
| 05–09 | Allocation engine, memberships, payments, renewals, cancellation |
| 10–12 | Attendance, test suite, Streamlit app |
| 13–14 | Analytics and reporting, auth / RBAC hardening |

<!-- VERIFY: mark each phase as done / in progress based on the repository. The spec itself marks only Phase 01 as completed. -->

---

## Documentation

Full design, DDL, algorithms and ADRs: [`docs/MASTER_TECHNICAL_SPECIFICATION.md`](docs/MASTER_TECHNICAL_SPECIFICATION.md) (also available as `Smart_Library_Master_Technical_Architecture_Specification_v1.0.pdf`).

<!-- Add application screenshots here -->

## License

<!-- No license information was provided. Add a LICENSE file and state it here. -->
