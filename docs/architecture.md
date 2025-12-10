# WhatsApp Expense Tracker Architecture (MVP)

## Requirements & Status
- [x] FastAPI app scaffold with `/health` and `/webhook` routes.
- [x] Text message handling: parse free-form text, create expenses, send confirmation via WhatsApp client stub.
- [x] SQLAlchemy models: `users`, `expenses`, `receipts`; SQLite fallback for local boot.
- [x] Basic WhatsApp client stub (send text, signature verification placeholder).
- [ ] Image handling: download media via WhatsApp Cloud API, store to S3, create `receipts` row, enqueue OCR job.
- [ ] OCR worker: consume queue, run Google Vision, parse totals/date/merchant, update receipts/expenses, notify user.
- [ ] Auth for web dashboard (email+password or phone+OTP).
- [ ] Frontend dashboard: login, list/filter expenses, view details + receipt image, edit category/notes/amount, monthly/category reports.
- [ ] Alembic migrations and production DB config (Postgres).
- [ ] Background queue (Redis + RQ/Celery) wiring for OCR jobs.
- [ ] Deployment/Docker: containerize API + worker; Postgres/Redis services; env-driven config.

## Backend (FastAPI)
- Webhook at `/webhook` handles WhatsApp Cloud API callbacks; text flow is implemented.
- Text is parsed into expense metadata using regex-based heuristics.
- Planned: image flow (media download -> S3 -> OCR queue) and worker processing.

## Frontend (Next.js)
- Minimal landing page calls `/api/expenses` (dummy data).
- Planned: authenticated dashboard for filtering/editing expenses and viewing receipts/reports.

## Data Storage
- SQLAlchemy models for `users`, `expenses`, and `receipts` map to PostgreSQL tables.
- SQLite fallback used locally for quick bootstrapping; migrations to be added later.
