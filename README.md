# Swarnabindu Drop Patient & Vaccination Management System
**Government Hospital System — Nepal**

A dedicated Django web application built for managing Swarnabindu vaccination sessions, patient registrations, vitals recording, exact Nepali age calculations, and official health reports.

---

## 🌟 Key Features

1. **Nepali Calendar (Bikram Sambat) Centralized Engine**
   - Natural BS Date conversion (`ad_to_bs`, `bs_to_ad`, `format_bs_date`).
   - Hospital dates displayed primarily in BS (e.g., `19 Ashoj 2083 BS`).

2. **Exact Age Calculation Service**
   - Calculates exact age on vaccination dates in `X years Y months Z days`.
   - Preserves historical age at vaccination permanently in DB records.
   - Categorizes patients into government reporting age brackets (0–6m, 6–12m, 1–2y, etc.).

3. **Patient & Shared Phone Rule**
   - Unique patient ID generation (e.g., `SW-000001`).
   - **Phone number is NOT unique**: Allows multiple siblings/children per guardian phone.

4. **Duplicate Patient Protection**
   - Proactively checks `Name + DOB`, `Guardian + Phone`, `Name + Guardian` before registration.
   - Issues non-blocking warnings with override confirmation.

5. **Manually Managed Vaccination Sessions**
   - No automatic date guessing or interval offsets.
   - Full date change audit logging (stores old date, new date, reason, user, and timestamp).

6. **Next Vaccination Relationship**
   - Links next appointment directly to a real `VaccinationSession`.

7. **Duplicate Vaccination Prevention**
   - Unique constraint on `(patient, vaccination_session)` both at DB level and form validation.

8. **Printable History Card**
   - Dedicated A4 print CSS formatting for patient records.

9. **Security, Roles & Audit Logging**
   - Server-side role enforcement (Administrator, Vaccination Operator, Read-only User).
   - Detailed audit trails for patient creation, session updates, and backups.

10. **Database Backups & Health**
    - `python manage.py backup_database` command.
    - System health monitor.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- `pip`

### 2. Setup Environment & Install Dependencies
```bash
# Extract zip archive
unzip swarnabindu_hospital.zip
cd swarnabindu_hospital

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Database Migration & Demo Data Seeding
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed fictitious demo data (creates admin, sessions, patients, shared phone numbers)
python manage.py seed_demo
```

### 4. Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open browser at: `http://localhost:8000`

---

## 🔑 Demo Credentials
| Role | Username | Password |
|---|---|---|
| **Administrator** | `admin` | `admin123` |
| **Vaccination Operator** | `operator` | `operator123` |

---

## 🧪 Running Automated Tests
To run the automated Django test suite verifying age calculation, duplicate phone support, session reschedule audit, and duplicate vaccination blocks:
```bash
python manage.py test hospital
```

---

## 💾 Database Backup Command
To create an instant timestamped snapshot of system data:
```bash
python manage.py backup_database
```
Backups are archived in the `backups/` directory.

---

## 🏥 Hospital LAN Deployment
To deploy across hospital local area network PCs:
1. Bind server: `python manage.py runserver 0.0.0.0:8000`
2. Add server IP (e.g. `192.168.1.100`) to `.env` file under `ALLOWED_HOSTS`.
3. Hospital workstations access system via `http://<SERVER_IP>:8000`.
