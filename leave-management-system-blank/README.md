# Dynamic PTO & Leave Management System (MVP)

A multi-location PTO and leave management system built with **FastAPI**, **SQLAlchemy**, and **React**.

## Key Features

1. **Location-Aware Holidays**: Actual calendar dates stored per location (e.g. Diwali in Bangalore, Deepavali in Singapore, Eid in Dubai, Thanksgiving in New York).
2. **Configurable Weekend Rules**: Configured per location (e.g. Saturday/Sunday for India/Singapore/USA, Friday/Saturday for UAE demo calendar).
3. **Location-Scoped Leave Types**: Leave types are scoped to Location. No direct associations between Employee and LeaveType.
4. **Deterministic Accrual Engine**: Monthly accrual rates mapped to Location + LeaveType, matched by Employee Grade and Tenure, strictly capping at `max_balance`.
5. **Idempotent Accruals**: Running monthly accrual multiple times for the same month never double-credits balances (guaranteed by `AccrualRecord` constraint).
6. **Atomic Pending Balance Reservation**: Leave requests immediately reserve requested working days as `pending`, preventing overbooking.
7. **Leave Cancellation**: Cancelling a pending leave request immediately releases the reserved pending days back to available balance.
8. **Real-time Pre-submission Preview**: Calculates exact working days (excluding location-specific holidays and weekends) and projects available balance before submission.

---

## Domain Relationships & Isolation

```
Employee (belongs to) ────► Location ────► LeaveType ────► AccrualPolicy
                             │
                             ├────► Holiday
                             │
                             └────► Weekend Config

Employee (creates) ───────► LeaveRequest (references Employee & LeaveType)
```

- Employee does NOT have direct relationship to LeaveType or AccrualPolicy.
- LeaveRequest does NOT store Location. Location is derived through Employee.
- Approval workflow is decoupled and reserved for future iteration.

---

## Quick Start

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Frontend UI: `http://localhost:3000`

### 3. Run Automated Tests
```bash
cd backend
python -m pytest tests -v
```

---

## Seed Data Summary

### Locations
- **BLR**: Bangalore Office (India) &bull; Weekend: Saturday & Sunday
- **SG**: Singapore Office (Singapore) &bull; Weekend: Saturday & Sunday
- **NY**: New York Office (USA) &bull; Weekend: Saturday & Sunday
- **DXB**: Dubai Office (UAE) &bull; Weekend: Friday & Saturday

### Employees & Initial Balances
- **E101**: Vijesh (Bangalore, Grade G5) &bull; PTO: 10.0, CASUAL: 5.0, SICK: 5.0 &bull; `vijeshthamodharan@gmail.com`
- **M201**: Kaviya (Bangalore, Grade G7, Engineering Director) &bull; PTO: 18.0, CASUAL: 6.0, SICK: 8.0 &bull; `anbarasukavya7@gmail.com`
- **ADMIN01**: Ahallya Nethra (Bangalore, Grade G8, HR Admin) &bull; PTO: 25.0, CASUAL: 8.0, SICK: 10.0 &bull; `ahallyanethrabl@gmail.com`
- **E102**: Mei Ling (Singapore, Grade G4) &bull; PTO: 8.0, SICK: 4.0
- **E103**: John Miller (New York, Grade G6) &bull; PTO: 15.0, SICK: 6.0
- **E104**: Fatima Al-Mansoor (Dubai, Grade G5) &bull; PTO: 12.0, CASUAL: 4.0, SICK: 5.0
