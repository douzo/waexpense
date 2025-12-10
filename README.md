# WA Expense Tracker

Early skeleton for a WhatsApp-driven expense tracker.

## Structure
- `backend/`: FastAPI app with WhatsApp webhook, simple parser, and SQLAlchemy models.
- `frontend/nextjs-app`: Minimal Next.js page consuming a dummy `/api/expenses` endpoint.
- `docs/`: Architecture notes.

## Backend quickstart
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Default config uses SQLite for local development. Configure environment variables for WhatsApp credentials and PostgreSQL when ready.
