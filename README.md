# Transporter Management System

A production Django application for managing fleet transport operations — drivers, vehicles, oil marketing company (OMC) relationships, compliance training, HSE procedures, and trip/violation records — for heavy vehicle transporters distributing fuel to pumps nationwide.

Deployed serverlessly on Vercel, backed by Postgres (Neon) and Cloudinary for media storage.

---

## Architecture

The system is a monolithic Django app deliberately kept simple where simplicity is warranted, with a few pragmatic adaptations for running Django on a serverless platform:

```
┌─────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│   Browser    │─────▶│  Vercel (Serverless)  │─────▶│  Neon Postgres   │
│  Tailwind /  │      │  Django via WSGI       │      │  (pooled, SSL)   │
│  vanilla JS  │◀─────│  api/index.py          │◀─────│                  │
└─────────────┘      └──────────┬────────────┘      └─────────────────┘
                                  │
                        ┌─────────┴─────────┐
                        │  Cloudinary CDN    │
                        │  (driver & user    │
                        │   photo uploads)   │
                        └────────────────────┘
```

**Why these choices:**

| Concern | Decision | Reason |
|---|---|---|
| Hosting | Vercel (`@vercel/python`, WSGI) | Zero-ops deploys straight from `main`; the whole app runs as one Python Lambda behind `api/index.py`. |
| Database | Postgres via `DATABASE_URL` (Neon), SQLite fallback | Serverless functions have no durable local disk — Postgres is required in production. SQLite remains for local dev with zero setup. |
| Media storage | Cloudinary (`django-cloudinary-storage`) | Vercel's filesystem is read-only/ephemeral per invocation; uploaded driver/user photos must live outside the function. Falls back to local `FileSystemStorage` when `CLOUDINARY_URL` isn't set (local dev). |
| Static files | WhiteNoise, plain (uncompressed) `StaticFilesStorage` | Serves static assets directly from the Lambda without a separate CDN hop. Deliberately *not* using WhiteNoise's `CompressedStaticFilesStorage` — its threaded gzip/brotli pass at `collectstatic` time has a known race against Django's duplicate-file cleanup. Compression still happens on the fly, at request time, via the middleware. |
| Static build | Tailwind CSS v3, compiled ahead of deploy | No JS bundler/runtime dependency in production — Tailwind's CLI output is checked into `static/build` and served as a plain asset. |

### Request flow

1. Vercel routes `/static/*` directly to the `staticfiles/` build output (see `vercel.json`).
2. All other paths hit `api/index.py`, which boots the Django WSGI app.
3. `LoginRequiredMiddleware` gate-keeps every view except the login route and static/media URLs — there is no public-facing surface by design; this is an internal operations tool.
4. Application logic lives in a single `dashboard` app, organized by domain entity (drivers, vehicles, companies, violations, training) rather than by technical layer.

---

## Data model

Eighteen models capturing the operational domain, roughly grouped as:

- **Fleet & ownership** — `Vehicle`, `VehicleMaker`, `VehicleOwner`, `Company` (OMCs), `Location`
- **Drivers & compliance** — `Driver`, `annual_training`, `annual_drill`, `DriverTrainingCompletion`, `DriverDrillCompletion`, `tool_box_meeting_topics`, `driver_tool_box_meeting_attended`
- **Safety & incidents** — `Violations`, `Driver_Violation`
- **Reference data** — `Procedure` (HSE / operations procedures), `User_Image`

The schema favors explicit junction tables (`Driver_Violation`, `driver_tool_box_meeting_attended`) over generic relations, keeping queries and admin views straightforward at the cost of some model count — a reasonable tradeoff for a system whose primary users are operations staff via Django admin and CRUD screens, not API consumers.

---

## Feature surface

| Module | Capabilities |
|---|---|
| **Drivers** | Full CRUD, photo upload, license/violation history, training & drill compliance tracking, tool-box meeting attendance |
| **Vehicles** | Full CRUD, filterable by OMC (TPPL / GO / PSO / APL), maker/owner association |
| **Companies (OMCs)** | CRUD for oil marketing company records |
| **Violations & HSE** | Violation catalog, per-driver violation logging, HSE and operational procedure reference library |
| **CSV import/export** | A generic, entity-driven pipeline (`dashboard/csv_io.py`) supporting export-with-column-selection and a guarded multi-step import flow: upload → column mapping → review → confirm, with a cancellable session-backed staging area |
| **Auth & access control** | Session-based auth, rate-limited login (`django-ratelimit`, 5 attempts/minute/IP), global `LoginRequiredMiddleware` |

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5.0 |
| Database | PostgreSQL (Neon, production) / SQLite (local dev) |
| Media storage | Cloudinary |
| Static files | WhiteNoise |
| Styling | Tailwind CSS 3.4 |
| Deployment | Vercel (`@vercel/python` + `@vercel/static-build`) |
| Auth | Django's built-in auth, session-backed |

---

## Local development

### Prerequisites
- Python 3.12+
- Node.js (for Tailwind's build step only — no runtime JS dependency)

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
DJANGO_SECRET_KEY=<generate one — never reuse the sample>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Optional locally — omit to use SQLite
# DATABASE_URL=postgres://user:password@host:5432/dbname

# Optional locally — omit to store uploads on local disk under media/
# CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
```

Run migrations and create an admin user:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Build Tailwind (one-off, or `--watch` while developing templates):

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/build/output.css --watch
```

Start the dev server:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/` and log in with the superuser account.

---

## Deployment (Vercel)

The project ships with `vercel.json` and `build_files.sh` already configured. These environment variables must be set in the Vercel project settings before deploying:

| Variable | Required | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | No default — the app refuses to start without it. |
| `DJANGO_ALLOWED_HOSTS` | Yes | Comma-separated. The current `VERCEL_URL` is auto-appended for preview deploys. |
| `DATABASE_URL` | Yes (production) | Neon (or any Postgres) connection string. SSL is enforced. |
| `CLOUDINARY_URL` | Yes (production) | Required for uploaded media to persist — Vercel's function filesystem is ephemeral. |
| `DJANGO_DEBUG` | No | Defaults to `False`. Never set `True` in production. |

Build pipeline (`build_files.sh`):

```bash
pip install -r requirements.txt --break-system-packages
rm -rf staticfiles
python manage.py collectstatic --noinput --upload-unhashed-files
```

The `--upload-unhashed-files` flag is required specifically because `django-cloudinary-storage` overrides Django's `collectstatic` to skip local file copying by default (it assumes Cloudinary is the static backend too). This project uses Cloudinary only for *media*, so the flag restores normal local static output.

Once environment variables are set, push to `main` — Vercel builds and deploys automatically.

---

## Project structure

```
mysite/              # Django project config (settings, urls, wsgi)
dashboard/           # Single application: models, views, admin, CSV import/export
api/index.py         # Vercel WSGI entrypoint
templates/           # Server-rendered templates, organized by entity
static/              # Tailwind source, compiled build output, vendor JS
build_files.sh        # Vercel build script
vercel.json            # Routing: /static/* served directly, everything else -> Django
```

---

## Known constraints & tradeoffs

- **No REST API.** The UI is server-rendered; there is currently no JSON API surface for external integrations.
- **Single Django app.** `dashboard` holds the entire domain. Reasonable at current scope; would benefit from splitting by bounded context (fleet, compliance, HSE) if the codebase grows significantly.
- **No automated test suite currently exercised in CI.** `dashboard/tests.py` exists as a scaffold; test coverage should be a priority before further feature work.
- **Media backend is Cloudinary-only in production**, with no fallback if Cloudinary is unreachable — acceptable for an internal ops tool, worth revisiting if uptime requirements tighten.
