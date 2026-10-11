# Smart Library & Study Center — React Web Application

A modern, high-performance, production-ready React 19 web application built with TypeScript, Vite, Tailwind CSS, TanStack Query, and Lucide React. Designed for front-desk operators, librarians, and facility managers of study centers and reading rooms.

---

## 🚀 Key Features & Modules

### 1. 📊 Executive Dashboard
- **Real-Time KPIs**: Active students, capacity utilization, current revenue collected, and pending dues.
- **Facility Utilization Metrics**: Physical desk occupancy, slot occupancy, and seat-hour occupancy.
- **Dynamic Shift Distribution**: Interactive Recharts breakdown across Morning, Afternoon, Evening, and Full Day slots.
- **3-Day Expiry Action Queue**: Direct renewal shortcuts for memberships expiring soon.

### 2. 🪑 Interactive Seat Floor Plan
- **100-Desk Grid Visualization**: Real-time status mapping (`Available`, `Occupied`, `Expiring Soon`, `Under Maintenance`).
- **Shift Perspective Filter**: Instant capacity matrix calculation for any date and shift.
- **Desk Inspector**: Detailed breakdown of desk amenities (power outlet, personal locker), active assignees, and occupancy duration.
- **Maintenance Lock / Unlock**: Immediate toggle mutation with optimistic updates.

### 3. 👨‍🎓 Student Management Directory
- **Instant Search & KYC Tracking**: Filter students by name, mobile, email, or government ID number.
- **Student Registration**: Validated admissions with duplicate mobile/email prevention.
- **Direct Student Actions**: View complete profile KYC, update contact info, or launch membership admission.
- **CSV Data Export**: One-click download of the complete student directory.

### 4. 📝 Memberships & Subscriptions
- **Admission Wizard**: Smart date picker with automated slot duration and fee calculation based on canonical shift rates.
- **Renewal Terminal**: Renew subscriptions with seamless seat or shift migration options.
- **Cancellation Workflow**: Formal membership termination with mandatory audit reason logging.
- **Real-time Status Badges**: Automatic derivation of `ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, and `CANCELLED`.

### 5. 💳 Cashier Terminal & Payment Ledger
- **Cashier Dues Collector**: Instant fee collection with support for partial payments and multi-channel receipts (`CASH`, `UPI`, `CARD`, `NET_BANKING`).
- **Complete Transaction Ledger**: Searchable payment audit trail with invoice references and transaction timestamps.
- **Receipt Modal**: Printable receipt modal with operator details and transaction metadata.
- **Admin Voiding**: Administrative payment voiding with audit remarks.

### 6. ⏱️ Attendance Rapid Terminal
- **Fast Check-in / Check-out**: Select student or scan ID to instantly stamp attendance.
- **Shift Boundary Validation**: Automated verification of student active subscription windows.
- **Daily Attendance Roster**: Complete roster showing entry time, exit time, total hours, and auto-checkout status.

### 7. 📈 Financial & Utilization Analytics
- **Custom Horizon Analytics**: Dynamic revenue queries across custom date ranges.
- **Payment Method Revenue Breakdown**: Stacked bar charts and pie charts of collection channels.
- **Financial Ledger Export**: CSV export of all financial transactions within the selected window.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | React 19 + TypeScript |
| **Build Tool** | Vite 8 |
| **Styling** | Tailwind CSS v4 |
| **Data Fetching & Cache** | TanStack Query v5 |
| **Routing** | React Router v7 |
| **HTTP Client** | Axios with interceptors & automatic JWT auth headers |
| **Charts & Visualizations** | Recharts |
| **Icons & Design** | Lucide React |
| **Testing** | Vitest + Testing Library + jsdom |

---

## 📦 Getting Started

### 1. Prerequisites
- Node.js `v20+` or `v22+`
- npm `v10+`

### 2. Environment Setup
Create a `.env` file in `frontend/react_app/` (or copy from `.env.example`):
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Development Server
```bash
# Navigate to the React app directory
cd frontend/react_app

# Install dependencies
npm install

# Start development server on http://localhost:5173
npm run dev
```

### 4. Automated Testing
Run the complete unit and integration test suite:
```bash
npm test
```

### 5. Production Build
Build optimized and type-checked assets for deployment:
```bash
npm run build
```
Built production assets will be generated in `dist/`.

---

## 🔐 Default Credentials (from backend seed)

- **Admin Account**: `admin` / `Admin@123`
- **Operator Account**: `librarian` / `Staff@123`
