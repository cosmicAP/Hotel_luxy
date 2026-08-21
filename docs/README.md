# Hotel Lux — Full Application Documentation

A complete, beginner-friendly guide to how the **Hotel Lux** booking web application works: its architecture, code flow, services, data, security, and deployment.

---

## Table of Contents

1. [What This App Is](#1-what-this-app-is)
2. [Big-Picture Architecture](#2-big-picture-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [The Data Model (Database)](#5-the-data-model-database)
6. [How a Request Flows Through Django](#6-how-a-request-flows-through-django)
7. [Every Page & Feature Explained](#7-every-page--feature-explained)
8. [Authentication & Users](#8-authentication--users)
9. [The AI Chatbot (DeepSeek)](#9-the-ai-chatbot-deepseek)
10. [Images & Cloudinary](#10-images--cloudinary)
11. [Emails](#11-emails)
12. [Security Features](#12-security-features)
13. [How Deployment Works (Render)](#13-how-deployment-works-render)
14. [Environment Variables](#14-environment-variables)
15. [Common Commands](#15-common-commands)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. What This App Is

**Hotel Lux** is a full-stack hotel booking website where visitors can:

- Browse a catalog of hotels with images, ratings, and nightly rates
- Search/filter by city and sort results
- View rooms available at each hotel
- Create an account, log in, and book rooms (with date validation & double-booking protection)
- View/cancel their own bookings
- Update their profile and change/reset their password
- Chat with an **AI assistant** (powered by the DeepSeek API) that answers questions using only the hotels in the database
- Admin manages everything (hotels, rooms, bookings) through Django's `/admin/` panel

---

## 2. Big-Picture Architecture

```
                     ┌────────────────────────────────────────────┐
                     │           THE INTERNET (browser)           │
                     └─────────────────────┬──────────────────────┘
                                           │ https://hotel-luxy.onrender.com
                                           ▼
                              ┌────────────────────────┐
                              │       RENDER           │  Hosts the Docker container
                              │  (cloud hosting)       │  Terminates HTTPS
                              │                        │
                              │  ┌──────────────────┐  │
                              │  │    GUNICORN      │  │  Python WSGI server (3 workers)
                              │  └────────┬─────────┘  │
                              │           ▼            │
                              │  ┌──────────────────┐  │
                              │  │      DJANGO      │  │  The web framework (your app)
                              │  └────────┬─────────┘  │
                              └───────────┼────────────┘
                                          │
              ┌───────────────────────────┼─────────────────────────────┐
              │                           │                             │
              ▼                           ▼                             ▼
   ┌──────────────────┐        ┌──────────────────┐          ┌──────────────────┐
   │  DATABASE        │        │  CLOUDINARY      │          │  DEEPSEEK API    │
   │  PostgreSQL      │        │  (image hosting) │          │  (AI chatbot)    │
   │  via NEON        │        │                  │          │                  │
   │  (or SQLite      │        │  <img src> →     │          │  POST → AI reply │
   │   in dev)        │        │  res.cloudinary  │          │                  │
   └──────────────────┘        └──────────────────┘          └──────────────────┘
```

**Three external services the app talks to:**
| Service | Role |
|---|---|
| **Render** | Hosts/runs the app, gives the public URL |
| **Neon (PostgreSQL)** | The persistent database (`DATABASE_URL`) |
| **Cloudinary** | Stores hotel images so they survive redeploys |

**And one AI provider:**
| Service | Role |
|---|---|
| **DeepSeek** | Powers the chatbot via its OpenAI-compatible API (`api.deepseek.com/v1`) |

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 5.2 (Python) |
| Web server (production) | Gunicorn |
| Static files | WhiteNoise |
| Database | PostgreSQL (prod, via Neon) / SQLite (dev) |
| Image storage | Cloudinary (`django-cloudinary-storage`) |
| AI chatbot | DeepSeek API (via `openai` python library) |
| Email | SMTP (Gmail) in prod, console in dev |
| Containerization | Docker + docker-compose |
| Cloud hosting | Render |
| Frontend | HTML templates + vanilla CSS/JS |

---

## 4. Project Structure

```
simpe_hotel/
├── manage.py                  # Django's entry-point CLI tool
├── requirements.txt           # Python dependencies
├── Dockerfile                 # How the container image is built
├── docker-compose.yml         # Local docker setup
├── entrypoint.sh              # Runs on container start (migrate, seed, start server)
├── render.yaml                # Render config (partial — env vars set manually)
├── setup.sh                   # Local setup helper (installs docker etc.)
├── .env                       # SECRET local env vars (gitignored, never commit!)
├── .env.example               # Template showing which env vars exist
├── SECURITY_REPORT.md         # Security audit + fixes
├── docs/                      # ← You are here
│
├── hotel_project/             # The PROJECT config package (not an app)
│   ├── settings.py            # All configuration
│   ├── urls.py                # Root URL routing
│   ├── wsgi.py                # Entry point for Gunicorn
│   └── asgi.py                # Async entry point (unused here)
│
└── hotel_alpha/               # THE APP (all business logic lives here)
    ├── models.py              # Database tables (Hotel, Room, Booking, ApiRateLimit)
    ├── views.py               # All the page logic (functions)
    ├── forms.py               # Booking form validation
    ├── urls.py                # App URL routes
    ├── admin.py               # Admin panel config
    ├── tests.py               # (empty placeholder)
    ├── static/hotel_alpha/    # CSS
    ├── templates/             # HTML files
    │   ├── base.html          # Shared layout (nav, footer, messages)
    │   ├── chatbot.html       # The AI chat widget
    │   ├── auth/              # login, signup, profile, password pages
    │   └── hotels/            # home, rooms, book_room, bookings pages
    ├── management/commands/   # Custom CLI commands
    │   ├── seed_data.py       # Fill DB with sample hotels/rooms
    │   ├── ensure_superuser.py# CHECK admin exists (no longer auto-creates!)
    │   └── upload_media.py    # Push local images → Cloudinary
    └── migrations/            # Database schema change history
```

---

## 5. The Data Model (Database)

Django uses an **ORM** — you write Python classes, Django converts them to database tables.

```
Hotel ──1──to──many──► Room ──1──to──many──► Booking
                        ▲                        │
                        └──  belongs to a User ──┘

ApiRateLimit  (separate table, used for chatbot throttling)
```

### Hotel (table: `hotel_alpha_hotel`)
| Field | Type | Notes |
|---|---|---|
| `id` | Auto field | Primary key |
| `name` | CharField | Hotel name |
| `city` | CharField | City |
| `description` | TextField | Max 1000 chars |
| `image` | ImageField | Stored under `hotels/…` (Cloudinary in prod) |
| `rating` | IntegerField | 1–5 stars |
| `rate_per_night` | DecimalField | ₹ per night |
| `created_at` | DateTimeField | Auto-set |

Default ordering: `-rating, name` (best-rated first).

### Room (table: `hotel_alpha_room`)
| Field | Type | Notes |
|---|---|---|
| `id` | Auto field | |
| `hotel` | ForeignKey → Hotel | `related_name='rooms'` so `hotel.rooms.all()` works |
| `room_type` | CharField | e.g. "Deluxe Room" |
| `capacity` | IntegerField | Max guests |
| `ac` | BooleanField | A/C yes/no |
| `room_no` | IntegerField | Unique per hotel |
| `price` | DecimalField | Optional; falls back to hotel's rate |
| `description` | TextField | |
| `amenities` | JSONField | e.g. `["WiFi", "TV"]` |

Constraint: a hotel cannot have two rooms with the same number.

### Booking (table: `hotel_alpha_booking`)
| Field | Type | Notes |
|---|---|---|
| `user` | ForeignKey → User | `SET_NULL` — stays even if user deleted |
| `user_name` | CharField | Guest name (typed, not forced from account) |
| `user_email` | EmailField | |
| `user_phone_no` | CharField | |
| `room` | ForeignKey → Room | `CASCADE` |
| `no_of_people` | IntegerField | `MinValueValidator(1)` — can't be 0/negative |
| `check_in_date` | DateField | |
| `check_out_date` | DateField | |
| `status` | CharField | `CONFIRMED` / `CANCELLED` / `COMPLETED` |
| `created_at` / `updated_at` | DateTimeField | |

**Computed properties (not stored in DB):**
- `total_cost` → `days × rate` where rate = `room.price` else `hotel.rate_per_night`
- `is_active` → `status == 'CONFIRMED'`

### ApiRateLimit (table: `hotel_alpha_apiratelimit`)
Used to throttle the public chatbot endpoint (anti-abuse).
| Field | Type | Notes |
|---|---|---|
| `key` | CharField (primary key) | e.g. `chatbot:1.2.3.4` |
| `count` | IntegerField | Requests in current window |
| `updated_at` | DateTimeField | Window start |

---

## 6. How a Request Flows Through Django

A typical "client hits a URL" journey:

```
1. Browser requests  https://hotel-luxy.onrender.com/hotel/3/rooms/
        │
2. Render/Cloudflare terminate TLS → forward to Gunicorn (gunicorn = WSGI server)
        │
3. Gunicorn hands the request to Django (hotel_project/wsgi.py → settings)
        │
4. Django runs MIDDLEWARE (in order from settings.py:47):
   SecurityMiddleware → WhiteNoise (static files) → Session → Common →
   CSRF → Auth → Messages → ClickJacking
        │
5. URL resolver (ROOT_URLCONF=hotel_project.urls)
   → matches 'hotel_alpha.urls' → path "hotel/<int:hotel_id>/rooms/"
   → calls views.hotel_rooms
        │
6. The view:
   a. Queries the DB (get_object_or_404(Hotel, id=3))
   b. Builds context dict {hotel, rooms}
   c. Returns render(request, "hotels/rooms.html", context)
        │
7. Django fills the template with data → returns full HTML
        │
8. Gunicorn sends HTML back to the browser → user sees the page
```

### URL map (hotel_alpha/urls.py)
| URL | View | Auth required? |
|---|---|---|
| `/` | `home` | No |
| `/signup/` | `signup_view` | No |
| `/login/` | `login_view` | No |
| `/logout/` | `logout_view` | No (uses POST) |
| `/hotel/<id>/rooms/` | `hotel_rooms` | No |
| `/room/<id>/book/` | `book_room` | **Yes** (`@login_required`) |
| `/bookings/` | `bookings_dashboard` | **Yes** |
| `/booking/<id>/cancel/` | `cancel_booking` | **Yes** |
| `/profile/` | `profile_view` | **Yes** |
| `/change-password/` | `change_password` | **Yes** |
| `/password-reset/` | `password_reset_request` | No |
| `/password-reset/<uid>/<token>/` | `password_reset_confirm` | No |
| `/api/chatbot/` | `chatbot_api` | No (but rate-limited) |
| `/admin/` | Django admin | **Admin** |

---

## 7. Every Page & Feature Explained

### Home page (`/`) — `home` view
- Reads `q` (search), `city` (filter), `sort` from the URL query string
- **Security:** `sort` is checked against a whitelist (`SORT_WHITELIST`) to prevent invalid input crashing the page
- Searches `name`, `city`, `description` with case-insensitive contains (`icontains`)
- Paginates 9 hotels per page
- Loads the chatbot widget on this page

### Hotel rooms page (`/hotel/<id>/rooms/`) — `hotel_rooms`
- Fetches one hotel + all its rooms via the `rooms` related-name

### Booking page (`/room/<id>/book/`) — `book_room`
- Requires login
- **Security (anti-double-booking):** wraps everything in `transaction.atomic()` and locks the room row with `select_for_update()`. This means if two users book the same room at the exact same time, one waits for the other — the overlap check then correctly rejects the second one.
- Validates dates and capacity in the form (`forms.py`)
- Sends a confirmation email
- On success → redirects to `/bookings/`

### My Bookings (`/bookings/`) — `bookings_dashboard`
- Shows only the logged-in user's bookings (`Booking.objects.filter(user=request.user)`)
- Optional `status` filter, paginated 10 per page

### Cancel booking (`/booking/<id>/cancel/`) — `cancel_booking`
- Fetches the booking **only if it belongs to the logged-in user** (`get_object_or_404(..., user=request.user)`) — a user cannot cancel someone else's booking
- Only `CONFIRMED` bookings can be cancelled

### Profile (`/profile/`) — `profile_view`
- Edits email / first name / last name (POST)

### Change password (`/change-password/`) — `change_password`
- Uses Django's `PasswordChangeForm`
- Calls `update_session_auth_hash()` so the user stays logged in after changing password

### Password reset (`/password-reset/…`) — 2 views
- `password_reset_request`: finds user by email, generates a signed token + base64-encoded user id, emails a reset link
- `password_reset_confirm`: verifies token & user id, lets the user set a new password
- The "user doesn't exist" case returns the same success message to avoid leaking which emails are registered

---

## 8. Authentication & Users

Django's built-in `django.contrib.auth` handles users/sessions — **no custom User model** is used.

- **Signup** uses `UserCreationForm` (username + password + confirm)
- **Login** uses `AuthenticationForm`
- Sessions are stored server-side; the browser only holds a session cookie
- Settings relevant to auth:
  - `LOGIN_URL = 'login'` → unauthenticated users get redirected to login
  - `LOGIN_REDIRECT_URL = 'home_allo'` → where you go after logging in
  - `SESSION_COOKIE_HTTPONLY = True` → JS can't read the session cookie
  - `SESSION_COOKIE_SECURE = True` (prod) → only sent over HTTPS
  - `SESSION_COOKIE_AGE = 86400` → session lasts 1 day
  - `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` → closing the browser logs you out

**Admin panel** at `/admin/` (Django's built-in). To create an admin:
```
python manage.py createsuperuser
```
**Important:** the old auto-creation of `admin/admin123` was removed for security.

---

## 9. The AI Chatbot (DeepSeek)

**Endpoint:** `POST /api/chatbot/` (JSON body: `{"message": "..."}`)

**Flow inside `chatbot_api` (views.py:307):**
1. **Rate limit check** — max 10 requests per 60 seconds per IP (DB-backed, works across gunicorn workers). Over limit → HTTP 429.
2. Parse JSON; reject missing/empty/too-long (>500 chars) messages.
3. Build a **system prompt** containing the real hotels from the database:
   ```
   You are a helpful hotel booking assistant for 'Hotel Lux.'
   You MUST answer using ONLY the hotel data below...
   AVAILABLE HOTELS:
   - The Grand Palace (Mumbai) | 5★ | ₹12000/night | ...
   ```
4. Call DeepSeek (`deepseek-chat` model, `max_tokens=300`, `temperature=0.7`) using the `openai` Python SDK pointed at `https://api.deepseek.com/v1`.
5. Return the AI reply as JSON: `{"reply": "..."}`.

**Frontend:** `templates/chatbot.html` is included on the home page. It's vanilla JS that POSTs the typed message with the CSRF token in a header, shows a "Thinking..." bubble, then the reply.

**Why the system prompt matters:** it forces the bot to only talk about hotels that actually exist in the DB (grounded answers, no hallucinated hotels) and to stay on-topic.

**Security:** rate-limited, CSRF-protected, message-length capped → prevents API-cost abuse and prompt-injection spam.

---

## 10. Images & Cloudinary

### The problem it solves
Render's filesystem is **ephemeral** — anything written to local disk disappears on redeploy/restart. Hotel images used to be stored on local disk (`media/`) and kept vanishing.

### How it works now
- In `settings.py:131-132`: **if `CLOUDINARY_URL` is set**, Django switches its media storage to `MediaCloudinaryStorage`. All image uploads then go to Cloudinary, and `hotel.image.url` returns a full Cloudinary URL (CDN-hosted).
- If `CLOUDINARY_URL` is **not** set, Django falls back to local disk (`media/`). This is the dev/fallback mode.

### Pushing existing images to Cloudinary
Run once after deploy (locally with `CLOUDINARY_URL` in `.env`, or in Render's shell):
```
python manage.py upload_media
```
This reads each hotel's image from local disk and re-saves it through Cloudinary storage — the DB doesn't change (same filenames), but now the images actually exist on Cloudinary.

---

## 11. Emails

Two kinds of emails exist:
1. **Booking confirmation** — sent on successful booking
2. **Password reset link** — sent on password reset request

**Backend choice (settings.py:135-147):**
- If `EMAIL_HOST` is set → **SMTP backend** (real emails sent via e.g. Gmail)
- Otherwise → **console backend** (emails printed to the server logs, nothing sent) — dev mode only

**Gmail specifics:** set `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`, plus `EMAIL_HOST_USER` (your Gmail) and `EMAIL_HOST_PASSWORD` (**an App Password**, not your normal Gmail password — generate one in Google Account → Security → App passwords).

---

## 12. Security Features

Everything here was added/fixed in the security hardening pass (see `SECURITY_REPORT.md`).

| Category | What's done |
|---|---|
| **DEBUG** | Forced `False` in production (`RENDER` env var check, settings.py:22-24). No more settings/source leaks on error pages. |
| **SECRET_KEY** | No weak default — production **refuses to start** without one (settings.py:15-19). |
| **HTTPS** | `SECURE_SSL_REDIRECT`, HSTS (1 year + subdomains + preload), secure session & CSRF cookies (prod only). |
| **CSRF** | Enabled everywhere; chatbot uses `X-CSRFToken` header (was previously exempt). `CSRF_TRUSTED_ORIGINS` includes `https://*.onrender.com`. |
| **Chatbot abuse** | Rate limit (10/60s/IP), `@require_POST`, 500-char message cap. |
| **Double-booking** | `transaction.atomic()` + `select_for_update()` in `book_room`. |
| **Sort injection/DoS** | `SORT_WHITELIST` in `home`. |
| **Admin backdoor** | Removed auto-creation of `admin/admin123`. `ensure_superuser` now only checks/warns. |
| **Guest count** | `MinValueValidator(1)` on `no_of_people`. |
| **Clickjacking / sniffing** | `X_FRAME_OPTIONS=DENY`, `SECURE_CONTENT_TYPE_NOSNIFF=True`. |
| **User enumeration** | Password-reset always shows the same message whether or not the email exists. |

---

## 13. How Deployment Works (Render)

### The deploy pipeline
```
git push (dev branch)  →  GitHub
      │
      ▼
Render detects the push → builds the Docker image
      │
Dockerfile:
  1. FROM python:3.11-slim
  2. pip install -r requirements.txt
  3. collectstatic (gathers CSS/admin assets into staticfiles/)
  4. (entrypoint.sh is set as ENTRYPOINT)
      │
      ▼
Container starts → entrypoint.sh runs:
  1. python manage.py migrate          ← apply DB schema changes
  2. python manage.py seed_data        ← add sample hotels if DB empty
  3. python manage.py ensure_superuser ← (now just checks, does NOT create)
  4. exec gunicorn ... --bind 0.0.0.0:${PORT}
      │
      ▼
App is live at https://hotel-luxy.onrender.com
```

### Important gotcha
`render.yaml` exists, but the service was **created manually in the Render dashboard**, so **Render does NOT read `render.yaml`** for env vars. That's why `DEBUG`, `CLOUDINARY_URL`, etc. must be added by hand in **Dashboard → Service → Environment**.

---

## 14. Environment Variables

All are read from `.env` (local) or Render's Environment tab (production).

| Variable | Required in prod? | Purpose |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Django signing key. **Booting fails without it.** |
| `DEBUG` | ✅ (should be `False`) | Debug mode — must be off in prod |
| `ALLOWED_HOSTS` | Optional | Comma-separated hosts; `.onrender.com` auto-added |
| `DATABASE_URL` | ✅ | Postgres connection string (Neon). Without it → SQLite (data loss on Render!) |
| `CLOUDINARY_URL` | ✅ (for images) | `cloudinary://API_KEY:API_SECRET@cloud_name` |
| `OPENAI_API_KEY` | ✅ (for chatbot) | DeepSeek API key |
| `EMAIL_HOST` | ✅ (for emails) | e.g. `smtp.gmail.com` |
| `EMAIL_PORT` | ✅ | `587` |
| `EMAIL_USE_TLS` | ✅ | `True` |
| `EMAIL_HOST_USER` | ✅ | Sender Gmail address |
| `EMAIL_HOST_PASSWORD` | ✅ | Gmail App Password |

`RENDER` is set automatically by Render (used to detect production).

---

## 15. Common Commands

Run everything from the `simpe_hotel/` directory.

```bash
# Local dev server (uses .env, SQLite, console emails)
python manage.py runserver

# Apply database migrations
python manage.py migrate

# Create a new migration after changing models.py
python manage.py makemigrations

# Fill the DB with sample hotels/rooms (idempotent — skips if data exists)
python manage.py seed_data

# Create an admin user (for /admin/)
python manage.py createsuperuser

# Push local images to Cloudinary (after setting CLOUDINARY_URL in .env)
python manage.py upload_media

# Run Django system checks
python manage.py check

# Production-style checks
python manage.py check --deploy

# Run the app in Docker locally
docker compose up -d --build

# Open a Python shell with the app loaded
python manage.py shell
```

---

## 16. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| **Deploy fails with `SECRET_KEY must be set in production`** | Add `SECRET_KEY` to Render env vars (Dashboard → Environment). |
| **Images broken (404) after deploy** | `CLOUDINARY_URL` missing in Render env → set it and run `python manage.py upload_media`. |
| **Error page leaks settings / shows "DEBUG=True"** | `DEBUG` is still `True` on Render → set `DEBUG=False`, redeploy. |
| **Emails never arrive** | Console backend active (no `EMAIL_HOST`) → add SMTP vars + Gmail App Password. |
| **Data disappears on redeploy** | Using SQLite because `DATABASE_URL` isn't set → set the Neon Postgres URL. |
| **Chatbot says "Too many requests"** | You hit 10 messages/60s from the same IP — wait a minute. |
| **Chatbot returns fallback "Sorry..."** | DeepSeek call failed → check `OPENAI_API_KEY` is set/valid. |
| **`admin/admin123` no longer works** | Good — auto-creation removed. Create a real admin with `createsuperuser`. |
| **Warnings in `check --deploy` about SECURE_* settings** | Normal in dev; production mode (`RENDER` set) enables them automatically. |
