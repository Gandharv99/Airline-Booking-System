# Airline Management System (Django + DRF)

Small backend for managing flights + seat-based bookings with a simple “hold → pay → confirm” flow.

## What’s inside
- **Flights**
  - List / retrieve flights (read-only API)
  - `available_seats` auto-calculated on flight creation (`rows * len(seat_configuration)`)

- **Bookings**
  - Create booking = **holds a seat** (default hold: **10 minutes**)
  - Pay for booking (mocked payment)
  - Cancel confirmed booking (marks cancelled + refunded, releases seat)
  - Background job expires held bookings and releases seats

## Tech stack
- Python + **Django 5.2**
- **Django REST Framework**
- **PostgreSQL**
- **APScheduler** (for expiring held seats)

---

## Local setup

### Prereqs
- Python 3.10+
- PostgreSQL running locally

### 1) Install deps
```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

## 2) Create database

Defaults are configured in `core/settings.py`:

- **DB:** `airline_booking_db`
- **User:** `postgres`
- **Pass:** `postgres`
- **Host:** `localhost`
- **Port:** `5432`

Create the DB (example):

```bash
createdb airline_booking_db
# or via psql:
# psql -U postgres -c "CREATE DATABASE airline_booking_db;"
```
## 3) Migrate + create admin user

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 4) Run server

```bash
python manage.py runserver
```
API base: http://127.0.0.1:8000/api/
Admin: http://127.0.0.1:8000/admin/

Note: the scheduler starts automatically on runserver (see booking/apps.py) and runs the expiry job every 60s.
