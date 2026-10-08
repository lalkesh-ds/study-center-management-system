# 📚 Smart Library & Study Center Management System

A production-grade space-as-a-service management platform for smart libraries, reading halls, and study centers managing **100 physical study desks** ($1 \to 100$) across **4 canonical shifts** daily.

Guarantees **zero double-bookings** under high concurrency through mathematical interval logic, PostgreSQL `btree_gist` multidimensional exclusion constraints, and pessimistic row locking (`SELECT ... FOR UPDATE`).

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------------------------+
| PRESENTATION LAYER (V1: Streamlit Front-Desk | V2: React Web / Mobile App)              |
+-----------------------------------------------------------------------------------------+
        |                                                                           |
        | HTTP REST / JSON API (Bearer JWT Authentication)                          |
        v                                                                           v
+-----------------------------------------------------------------------------------------+
| FASTAPI BACKEND ASGI APPLICATION (:8000)                                                |
|  - Auth & RBAC (Argon2id + JWT)               - Master Data (Students, Seats, Shifts)   |
|  - Admission Engine (Pessimistic Locking)     - Financial Ledger (Partial Dues & Voids) |
|  - Attendance Tracker (Shift Grace Window)    - Capacity Analytics (300 Slots / 1600h)  |
+-----------------------------------------------------------------------------------------+
        |                                                                           |
        | SQLAlchemy 2.0 ORM (Parameterized Queries)                                |
        v                                                                           v
+-----------------------------------------------------------------------------------------+
| POSTGRESQL 15+ DATABASE ENGINE (with btree_gist extension)                               |
|  - Table: seats (1 to 100)                    - Table: shifts (4 canonical shifts)      |
|  - Table: students                            - Table: memberships                      |
|  - Table: payments (immutable ledger)         - Table: attendance                       |
|  - Table: users & audit_logs                  - View: v_memberships_expanded            |
|  * CONSTRAINT exclude_seat_time_conflict GiST (seat_id WITH =, date_range WITH &&, ...)  |
|  * CONSTRAINT exclude_student_time_conflict GiST (student_id WITH =, ...)               |
+-----------------------------------------------------------------------------------------+
```

---

## 🕒 Facility Operating Shifts & Invariants

Operating Hours: **07:00 AM – 11:00 PM Daily (16 Operating Hours / Day)**

| Shift Name | Start Time | End Time | Discrete Minutes | Duration | Default Fee |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Morning** | 07:00 AM | 11:00 AM | $[420, 660)$ | 4 Hours | ₹800.00 |
| **Afternoon** | 11:00 AM | 03:00 PM | $[660, 900)$ | 4 Hours | ₹800.00 |
| **Evening** | 03:00 PM | 11:00 PM | $[900, 1380)$ | 8 Hours | ₹1,200.00 |
| **Full Day** | 07:00 AM | 11:00 PM | $[420, 1380)$ | 16 Hours | ₹2,200.00 |

### Core Mathematical Invariants
1. **Half-Open Intervals**: Daily shifts are defined on $[T_{\text{start}}, T_{\text{end}})$. Consecutive shifts (e.g. 07–11 and 11–15) touch at 11:00 without collision ($\max(S_1, S_2) < \min(E_1, E_2) \implies \text{False}$).
2. **Inclusive Calendar Dates**: Subscriptions run on $[D_{\text{start}}, D_{\text{end}}]$ inclusive ($S_1 \le E_2 \land S_2 \le E_1$).
3. **Derived Statuses**: Only `ACTIVE` and `CANCELLED` are stored in the database. `EXPIRING_SOON` and `EXPIRED` are derived dynamically on read to eliminate stale cron states and table write bloat.
4. **Capacity Paradox Resolved**:
   - **Physical Desk Utilization**: $\frac{\text{Occupied Desks Today}}{100} \times 100\%$
   - **Slot-Capacity Occupancy**: $\frac{\text{Slots Consumed Today}}{300} \times 100\%$ (Full Day counts as 3 slots)
   - **Seat-Hour Occupancy**: $\frac{\text{Seat-Hours Booked Today}}{1,600} \times 100\%$

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 15+ (Local or Cloud: Neon, Supabase, RDS)

### 2. Installation
```bash
# Clone repository
git clone https://github.com/your-repo/library-management-system.git
cd "library management system"

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and set your database connection URL:
```bash
cp .env.example .env
```
In `.env`:
```ini
DATABASE_URL=postgresql+psycopg://postgres:your_password@your_host:5432/library_db
SECRET_KEY=your_cryptographic_secret_key_minimum_32_characters
```

### 4. Database Setup & Seed Data
Run Alembic migrations to construct the GiST exclusion schema, then seed 100 seats, 4 shifts, and default admin:
```bash
# Apply migrations
python -m alembic upgrade head

# Seed 100 physical desks, shifts, and admin user
python scripts/seed_data.py
```

### 5. Start the FastAPI Backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 6. Start the Streamlit Front-Desk UI
In a separate terminal:
```bash
streamlit run frontend/streamlit_app/app.py
```
- Open browser at [http://localhost:8501](http://localhost:8501)
- Default credentials:
  - **Username**: `admin`
  - **Password**: `Admin@Library2026!`

---

## 🖥️ Streamlit Front-Desk Portal Modules

| Module Page | Description |
| :--- | :--- |
| **🪑 1. Seat Grid** | Interactive $10 \times 10$ floor plan of 100 desks with live shift color-coding (🟢 Free, 🟡 Partial, 🟣 Full Day, 🔴 Maintenance). Toggle seat maintenance on/off. |
| **👨‍🎓 2. Students** | Searchable student directory, 10-digit mobile validation, identity proof capture, and complete profile history. |
| **📝 3. Memberships** | Deterministic seat reservation modal with automatic collision rejection, subscription renewals (`renewed_from_id` lineage), and immediate seat release cancellations. |
| **💳 4. Cashier Payments** | Dues installment collection, printable receipt generation (`RCP-YYYYMMDD-XXXX`), and admin-protected 24-hour payment voiding. |
| **⏱️ 5. Attendance** | Front-desk rapid search check-in / check-out terminal, operating shift grace threshold ($\pm 30$ mins), and live daily roster with study session durations. |
| **📊 6. Analytics Dashboard** | Plotly charts for 300-slot occupancy, time-weighted 1,600-hour utilization, expiring renewal action queue, and revenue collections by channel (UPI, Cash, Card, Net Banking). |

---

## 🧪 Automated Testing Suite

The repository includes a comprehensive test suite (54 automated tests) verifying all constraints, pessimistic locking, boundary handover math, and end-to-end operational lifecycles:

```bash
# Run all tests
python -m pytest backend/tests/ -v
```

### Test Breakdown
- `test_allocation_engine.py`: Half-open math, boundary handovers, full-day blocking, and concurrency.
- `test_memberships.py`: Admissions, discount validations, overpayment rejections, renewals, cancellations.
- `test_payments.py`: Multi-installment tracking, partial dues clearance, payment voiding security.
- `test_attendance.py`: Daily check-in/out, shift grace windows, duplicate prevention.
- `test_analytics.py`: Utilization rates (100 seats, 300 slots, 1600 hours), revenue breakdowns.
- `test_auth.py`: JWT generation, password verification (Argon2id/Bcrypt), role-based access control (ADMIN vs STAFF).
- `test_e2e_workflow.py`: Complete simulated day-in-the-life business workflow.

---

## 📄 Documentation & PDF Specification
- Master Specification: [`docs/MASTER_TECHNICAL_SPECIFICATION.md`](docs/MASTER_TECHNICAL_SPECIFICATION.md)
- Publication-Grade 24-Page PDF: [`Smart_Library_Master_Technical_Architecture_Specification_v1.0.pdf`](Smart_Library_Master_Technical_Architecture_Specification_v1.0.pdf)
