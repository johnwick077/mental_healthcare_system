# Mental Healthcare Patient Observation & Resource Management System

Django-based system for digitizing daily patient observations and personal care
resource requests in mental healthcare settings. Does not diagnose — only
records observations and assists counsellors in prioritization via a
non-clinical Patient Observation Index (POI).

## Tech Stack
Django 5+/6, MySQL, Bootstrap 5, Chart.js, ReportLab

## Setup
1. `python -m venv venv` and activate it
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your values
4. Create the MySQL database: `CREATE DATABASE mhcore_db CHARACTER SET utf8mb4;`
5. `python manage.py migrate`
6. `python manage.py createsuperuser` (then set role=Admin in /admin/)
7. Optional: `python manage.py seed_data` for sample data
8. `python manage.py runserver`

## Roles
Admin, Counsellor, Store Manager — each with a dedicated dashboard.