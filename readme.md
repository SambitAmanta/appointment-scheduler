# Appointment Scheduling System – Backend

A production-ready backend for a full-stack appointment scheduling platform.  
Includes **JWT auth**, role-based permissions, scheduling logic with overlap prevention, analytics APIs, Celery tasks, and email notifications.

---

## ⚙️ Features

- Role-based authentication (`admin`, `provider`, `customer`)
- Services, appointments, availability, and booking workflows
- Overlap & buffer-time validation
- Admin & provider analytics (trends, revenue, utilization)
- CSV export endpoint
- Celery async tasks for notifications & reminders
- Optional WebSocket support (Django Channels)
- DRF pagination, filtering, and permissions

---

## 🛠️ Setup

```sh
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
```

## 📡 API Overview

| Endpoint             | Description                    |
| -------------------- | ------------------------------ |
| `/auth/register`     | Register user (role-based)     |
| `/auth/login`        | JWT login                      |
| `/services/`         | CRUD services (admin/provider) |
| `/appointments/`     | Book, reschedule, cancel       |
| `/availability/`     | Provider slot management       |
| `/dashboard/*`       | Analytics endpoints            |
| `/dashboard/export/` | CSV export                     |

## 🔐 Roles & Permissions

| Action                     | Customer | Provider | Admin |
| -------------------------- | -------- | -------- | ----- |
| Book appointment           | ✅       | ❌       | ❌    |
| Approve/reject appointment | ❌       | ✅       | ✅    |
| Create/edit service        | ❌       | ✅       | ✅    |
| See analytics              | Limited  | ✅       | ✅    |
