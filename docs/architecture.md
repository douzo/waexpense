# WhatsApp Expense Tracker Architecture (MVP)

## Backend (FastAPI)
- Webhook endpoint at `/webhook` handles WhatsApp Cloud API callbacks.
- Text messages are parsed into expense metadata using regex-based heuristics.
- Future: image handling via media download + OCR worker queue.

## Frontend (Next.js)
- Minimal landing page that calls `/api/expenses` to display expenses (dummy data for now).
- Will evolve into authenticated dashboard for filtering and editing expenses.

## Data Storage
- SQLAlchemy models for `users`, `expenses`, and `receipts` map to PostgreSQL tables.
- SQLite fallback used locally for quick bootstrapping; migrations to be added later.
