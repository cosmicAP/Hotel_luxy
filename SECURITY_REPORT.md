# Hotel Lux — Security Audit & Remediation Report

**Date:** 2026-08-07
**Target:** `~/simpe_hotel` (deployed at https://hotel-luxy.onrender.com/)
**Status:** All changes made on branch `dev` (not yet committed). `main` was merged into `dev` first; `dev` was already up to date.

---

## Executive Summary

The live site was running with `DEBUG=True`, which leaks settings, source code and environment variables through error pages. A hardcoded `admin/admin123` superuser is auto-created on every deploy, giving anyone full admin access. The public AI chatbot had no rate limiting, letting anyone burn DeepSeek API credits. These were the most critical issues. All are now fixed in code on `dev`.

---

## Findings & Fixes

### CRITICAL

| # | Issue | Evidence | Fix applied |
|---|-------|----------|-------------|
| 1 | **`DEBUG=True` on production** — live 404/500 pages leak settings, `ALLOWED_HOSTS`, source tracebacks | Confirmed via `?sort=price;select` returning HTTP 500 with settings dump | `settings.py`: `DEBUG` is force-disabled whenever `RENDER` env var is set (Render sets this automatically), regardless of the env file |
| 2 | **Admin backdoor `admin/admin123`** — auto-created on every deploy (`ensure_superuser.py`) | File content + git history | `ensure_superuser.py` rewritten to only **check** and warn; it never creates credentials. Create superusers manually with `createsuperuser` |
| 3 | **Chatbot API unauthenticated, `@csrf_exempt`, no rate limit** — anyone could spam → unlimited DeepSeek spend + prompt injection | Confirmed live: unauthenticated POST returned AI reply | Rate limiting (DB-backed, works across gunicorn workers) 10 req / 60 s per IP; `@require_POST`; 500-char message cap; CSRF re-enabled with `X-CSRFToken` from the frontend |
| 4 | **Real DeepSeek API key in `.env`** (gitignored, but still a live credential on disk) | `~/.env` contains `sk-9f73...` | Key not committed (good). Rotate it anyway (see "Manual actions required"). New random `SECRET_KEY` generated for local `.env` |

### HIGH

| # | Issue | Evidence | Fix applied |
|---|-------|----------|-------------|
| 5 | **Booking double-booking race (TOCTOU)** — overlap check only in the form; two simultaneous submits both pass | `forms.py` `clean()` runs outside any lock | `book_room` now wraps creation in `transaction.atomic()` + `Room.objects.select_for_update()` so concurrent bookings serialize |
| 6 | **`sort` GET param passed directly to `order_by()`** — confirmed HTTP 500 DoS vector | `?sort=price;select` → 500 | `SORT_WHITELIST` validated in `views.py`; invalid values fall back to `-rating` |
| 7 | **Emails never delivered** — `EMAIL_BACKEND=console`, `fail_silently=True`; password-reset tokens printed to Render logs | `settings.py:120`, `views.py:122` | `EMAIL_BACKEND` now uses real SMTP when `EMAIL_HOST` is set; booking emails use `fail_silently=False` and log errors. (Requires SMTP creds — see manual actions) |
| 8 | **`SESSION_COOKIE_SECURE=False`, no HSTS, no SSL redirect** | `settings.py:133-141` | `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` = `not DEBUG`; production now sets `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, `SECURE_HSTS_SECONDS=31536000` |
| 9 | **No rate limiting on login/signup** — brute-force friendly, especially with the `admin123` backdoor | Code review | Partially mitigated by fixing #2. Full login rate limiting is deferred (see recommendations) |
| 10 | **`no_of_people` accepts 0/negative** | `models.py:58` | Added `MinValueValidator(1)` |

### LOW

| # | Issue | Fix |
|---|-------|-----|
| 11 | User enumeration via signup/login error messages | Deferred — use `django-ratelimit` on auth views |
| 12 | `CSRF_TRUSTED_ORIGINS` missing `.onrender.com` | Added `https://*.onrender.com` |
| 13 | `test_post.py` committed to repo | Deferred — harmless dev artifact; consider removing |
| 14 | Media falls back to ephemeral disk if `CLOUDINARY_URL` unset | Not a security issue; verify Cloudinary is configured on Render |

---

## Manual Actions Required (not fixable in code)

1. **Rotate the DeepSeek API key.** The key in `.env` (`sk-9f73...`) should be revoked on the DeepSeek dashboard and replaced with a new one.
2. **Remove / reset the live `admin` account.** The currently deployed database almost certainly has `admin/admin123`. Log into `/admin/` and change the password immediately (or delete the account and recreate via `createsuperuser`). After deploying `dev`, the auto-creation code no longer runs, but the *existing* account persists.
3. **Set env vars in the Render dashboard** (the service was created manually, so `render.yaml` values are not applied):
   - `DEBUG` = `False`  ← most important
   - `SECRET_KEY` = a fresh random value (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail app password) — otherwise emails stay console-only
   - Confirm `DATABASE_URL` is set (Postgres, not SQLite) and `CLOUDINARY_URL` is set
4. **Redeploy** from `dev`, then verify: a visit to `/nonexistent-page/` should no longer show the `DEBUG=True` message.

---

## Files Changed

- `hotel_project/settings.py` — DEBUG guard, secure cookies/HSTS/SSL, CSRF trusted origins, SECRET_KEY requirement, SMTP email
- `hotel_alpha/views.py` — sort whitelist, atomic booking, chatbot rate limit + CSRF + length cap
- `hotel_alpha/models.py` — `ApiRateLimit` model, `MinValueValidator` on `no_of_people`
- `hotel_alpha/migrations/0006_apiratelimit_alter_booking_no_of_people.py` — new migration
- `hotel_alpha/templates/chatbot.html` — CSRF token header in fetch
- `hotel_alpha/management/commands/ensure_superuser.py` — no longer creates credentials
- `.env.example`, `.env` (local), `.gitignore` — key rotation, `.venv/` ignore

## Verification Performed

- `python manage.py check` → no issues
- `python manage.py check --deploy` (with `RENDER=true`) → no issues
- Rate limiter unit-tested → allows 3, blocks on 4th
- CSRF: POST without token → 403; with token → passes
- Production settings confirmed: `DEBUG=False`, secure cookies on, HSTS on, SSL redirect on
