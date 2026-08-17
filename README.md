# Transporter Management System

[![Python](https://img.shields.io/badge/python-3.12+-blue)]()
[![Django](https://img.shields.io/badge/django-5.0-092E20)]()
[![Deployment](https://img.shields.io/badge/deployed%20on-Vercel-black)]()
[![Tests](https://img.shields.io/badge/tests-present%2C%20not%20in%20CI-yellow)]()

A production Django application for managing fleet transport operations: drivers, vehicles, oil marketing company (OMC) relationships, compliance training, HSE procedures, and violation records, built for heavy vehicle transporters distributing fuel to pumps nationwide.

Deployed serverlessly on Vercel, backed by Postgres (Neon) and Cloudinary for media storage.

## Table of contents

1. [Architecture](#architecture)
2. [Data model](#data-model)
3. [Feature surface](#feature-surface)
4. [Security](#security)
5. [Tech stack](#tech-stack)
6. [Local development](#local-development)
7. [Deployment (Vercel)](#deployment-vercel)
8. [Project structure](#project-structure)
9. [Known constraints and tradeoffs](#known-constraints-and-tradeoffs)

## Architecture

The system is a monolithic Django app, kept deliberately simple where simplicity is warranted, with a few pragmatic adaptations for running Django on a serverless platform.

```
┌──────────────┐      ┌───────────────────────┐      ┌──────────────────┐
│   Browser     │─────▶│  Vercel (Serverless)   │─────▶│  Neon Postgres    │
│  Tailwind /   │      │  Django via WSGI        │      │  (pooled, SSL)    │
│  vanilla JS   │◀─────│  api/index.py           │◀─────│                   │
└──────────────┘      └───────────┬─────────────┘      └──────────────────┘
                                    │
                          ┌─────────┴──────────┐
                          │  Cloudinary CDN     │
                          │  (driver and user   │
                          │   photo uploads)    │
                          └─────────────────────┘
```

**Why these choices**

| Concern | Decision | Reason |
|---|---|---|
| Hosting | Vercel (`@vercel/python`, WSGI) | Zero ops deploys straight from `main`. The whole app runs as one Python Lambda behind `api/index.py`. |
| Database | Postgres via `DATABASE_URL` (Neon), SQLite fallback | Serverless functions have no durable local disk, so Postgres is required in production. SQLite remains for local dev with zero setup. |
| Media storage | Cloudinary (`django_cloudinary_storage`) | Vercel's filesystem is read only and ephemeral per invocation, so uploaded driver and user photos must live outside the function. Falls back to local `FileSystemStorage` when `CLOUDINARY_URL` isn't set (local dev). |
| Static files | WhiteNoise, plain (uncompressed) `StaticFilesStorage` | Serves static assets directly from the Lambda without a separate CDN hop. Deliberately not using WhiteNoise's `CompressedStaticFilesStorage`, since its threaded gzip/brotli pass at `collectstatic` time has a known race against Django's duplicate file cleanup. Compression still happens on the fly, at request time, via the middleware. |
| Static build | Tailwind CSS v3, compiled ahead of deploy | No JS bundler or runtime dependency in production. Tailwind's CLI output is checked into `static/build` and served as a plain asset. |

### Request flow

1. Vercel routes `/static/*` directly to the `staticfiles/` build output (see `vercel.json`).
2. All other paths hit `api/index.py`, which boots the Django WSGI app.
3. `LoginRequiredMiddleware` gate keeps every view except the login route and static or media URLs. There is no public facing surface by design; this is an internal operations tool.
4. A separate `superuser_required` decorator further restricts destructive or administrative actions (record deletion, company management) to superuser accounts, on top of the general login requirement.
5. Application logic lives in a single `dashboard` app, organized by domain entity (drivers, vehicles, companies, violations, training) rather than by technical layer.

## Data model

Eighteen models capture the operational domain, grouped roughly as:

- **Fleet and ownership**: `Vehicle`, `VehicleMaker`, `VehicleOwner`, `Company` (OMCs), `Location`
- **Drivers and compliance**: `Driver`, `annual_training`, `annual_drill`, `annual_training_driver`, `annual_drill_driver`, `DriverTrainingCompletion`, `DriverDrillCompletion`, `tool_box_meeting_topics`, `driver_tool_box_meeting_attended`
- **Safety and incidents**: `Violations`, `Driver_Violation`
- **Reference data**: `Procedure` (HSE and operations procedures), `User_Image`

The schema favors explicit junction tables (`Driver_Violation`, `driver_tool_box_meeting_attended`, `annual_training_driver`, `annual_drill_driver`) over generic relations, keeping queries and admin views straightforward at the cost of some model count. That is a reasonable tradeoff for a system whose primary users are operations staff working through Django admin and CRUD screens, not API consumers.

Key records (`Driver`, `Vehicle`, `Company`) use soft deletion rather than hard deletion: rows are flagged inactive and excluded from normal listings instead of being removed from the database, preserving historical and audit data.

An expiry status service (`dashboard/services.py`) computes a `Valid`, `Close to Expiry`, or `Expired` status for every tracked date field on a driver or vehicle (license validity, CNIC validity, insurance, fitness, tax, route permits, and more), so compliance risk is visible on the record itself rather than requiring a separate report.

## Feature surface

| Module | Capabilities |
|---|---|
| Drivers | Full CRUD, photo upload, license and violation history, training and drill compliance tracking, tool box meeting attendance, automatic expiry status on every tracked license or certification date |
| Vehicles | Full CRUD, filterable by OMC (TPPL, GO, PSO, APL), maker and owner association, automatic expiry status on tax, fitness, insurance, and permit dates |
| Companies (OMCs) | CRUD for oil marketing company records |
| Violations and HSE | Violation catalog, per driver violation logging, HSE and operational procedure reference library |
| CSV import and export | A generic, entity driven pipeline (`dashboard/csv_io.py`) supporting export with column selection and a guarded multi step import flow (upload, column mapping, review, confirm) with a cancellable session backed staging area |
| Access control | Session based auth, rate limited login (`django_ratelimit`, 5 attempts per minute per IP), global `LoginRequiredMiddleware`, and a `superuser_required` decorator restricting destructive actions |
| Data integrity | Soft delete on drivers, vehicles, and companies; unique constraint on active driver CNIC to prevent duplicate active records while still allowing historical ones |

## Security

- Every route except login and static or media assets requires an authenticated session, enforced globally by `LoginRequiredMiddleware`.
- Destructive and administrative actions (deleting records, managing companies) additionally require superuser status, enforced by a dedicated decorator and covered by regression tests.
- Login is rate limited to 5 attempts per minute per IP address using `django_ratelimit`.
- `DJANGO_SECRET_KEY` has no default; the application refuses to start without one explicitly set.
- `DJANGO_DEBUG` defaults to `False` and must be deliberately overridden for local development.
- Database connections to Neon enforce SSL.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5.0 |
| Database | PostgreSQL (Neon, production), SQLite (local dev) |
| Media storage | Cloudinary |
| Static files | WhiteNoise |
| Styling | Tailwind CSS 3.4 |
| Deployment | Vercel (`@vercel/python` and `@vercel/static-build`) |
| Auth | Django's built in auth, session backed |
| Testing | Django's test framework (`dashboard/tests.py`), covering soft delete behavior, the `superuser_required` decorator, the expiry status service, and `LoginRequiredMiddleware`, not currently run in CI |

## Local development

### Prerequisites

- Python 3.12 or newer
- Node.js (for Tailwind's build step only; there is no runtime JS dependency)

### Setup

```bash
git clone https://github.com/noorrbutt/Transporter-Management-System.git
cd Transporter-Management-System

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
npm install
```

Create a `.env` file in the project root:

```bash
DJANGO_SECRET_KEY=<generate one, never reuse the sample>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Optional locally, omit to use SQLite
# DATABASE_URL=postgres://user:password@host:5432/dbname

# Optional locally, omit to store uploads on local disk under media/
# CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
```

Run migrations and create an admin user:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Build Tailwind (one off, or with `--watch` while developing templates):

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/build/output.css --watch
```

Run the test suite:

```bash
python manage.py test
```

Start the dev server:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/` and log in with the superuser account.

## Deployment (Vercel)

The project ships with `vercel.json` and `build_files.sh` already configured. These environment variables must be set in the Vercel project settings before deploying:

| Variable | Required | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | No default. The app refuses to start without it. |
| `DJANGO_ALLOWED_HOSTS` | Yes | Comma separated. The current `VERCEL_URL` is auto appended for preview deploys. |
| `DATABASE_URL` | Yes, production | Neon (or any Postgres) connection string. SSL is enforced. |
| `CLOUDINARY_URL` | Yes, production | Required for uploaded media to persist, since Vercel's function filesystem is ephemeral. |
| `DJANGO_DEBUG` | No | Defaults to `False`. Never set to `True` in production. |

Build pipeline (`build_files.sh`):

```bash
pip install -r requirements.txt --break-system-packages
rm -rf staticfiles
python manage.py collectstatic --noinput --upload-unhashed-files
```

The `--upload-unhashed-files` flag is required specifically because `django_cloudinary_storage` overrides Django's `collectstatic` to skip local file copying by default, since it assumes Cloudinary is the static backend too. This project uses Cloudinary only for media, so the flag restores normal local static output.

Once environment variables are set, push to `main` and Vercel builds and deploys automatically.

## Project structure

```
mysite/              Django project config: settings, urls, wsgi
dashboard/           Single application: models, views, admin, CSV import/export, services, tests
api/index.py         Vercel WSGI entrypoint
templates/           Server rendered templates, organized by entity
static/              Tailwind source, compiled build output, vendor JS
build_files.sh        Vercel build script
vercel.json           Routing: /static/* served directly, everything else to Django
```

## Known constraints and tradeoffs

- **No REST API.** The UI is server rendered; there is currently no JSON API surface for external integrations.
- **Single Django app.** `dashboard` holds the entire domain. Reasonable at current scope; would benefit from splitting by bounded context (fleet, compliance, HSE) if the codebase grows significantly.
- **Tests exist but are not run in CI.** `dashboard/tests.py` covers soft delete behavior, the `superuser_required` decorator, the expiry status service, and `LoginRequiredMiddleware`. Wiring this into CI is a near term priority rather than writing tests from scratch.
- **Media backend is Cloudinary only in production**, with no fallback if Cloudinary is unreachable. Acceptable for an internal ops tool, worth revisiting if uptime requirements tighten.
