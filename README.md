# WA Expense Tracker

WhatsApp-driven expense tracker skeleton (FastAPI backend + Next.js frontend).

## Structure
- `backend/`: FastAPI app with WhatsApp webhook, simple parser, and SQLAlchemy models.
- `frontend/nextjs-app`: Minimal Next.js page consuming a dummy `/api/expenses` endpoint.
- `docs/`: Architecture notes.

## Backend: Run & Test

### 1) Prereqs
- Python 3.11+
- SQLite works by default; Postgres optional (`DATABASE_URL`).
- WhatsApp Cloud API creds if you want to hit the real Graph API.

### 2) Environment
Create `backend/.env` (or export in your shell). Defaults to SQLite and placeholder tokens.
```
APP_NAME="WA Expense Tracker"
DEBUG=true
DATABASE_URL="sqlite:///./app.db"           # or postgres://user:pass@host:5432/dbname
WHATSAPP_VERIFY_TOKEN="dev-verify-token"    # used for webhook verification GET
WHATSAPP_APP_SECRET="app-secret"            # used for X-Hub-Signature-256 verification
WHATSAPP_ACCESS_TOKEN="your-wa-access-token"
WHATSAPP_PHONE_NUMBER_ID="your-wa-phone-id"
```

### 3) Install deps
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Run the API
```
uvicorn app.main:app --reload
```
Server: http://127.0.0.1:8000

### 5) Smoke tests (local)
- Health: `curl http://127.0.0.1:8000/health`
- Expenses stub: `curl http://127.0.0.1:8000/api/expenses`

### 6) Simulate a WhatsApp text webhook (no signature)
Run while the server is up:
```
curl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
        "entry": [{
          "changes": [{
            "value": {
              "messages": [{
                "from": "15551234567",
                "id": "wamid.ID",
                "timestamp": "1713120000",
                "type": "text",
                "text": { "body": "Dinner 23.5 USD restaurant" }
              }],
              "contacts": [{ "wa_id": "15551234567" }]
            }
          }]
        }]
      }'
```
Expected: text parser extracts fields, expense is saved (SQLite), and a confirmation send is attempted (will log if WA creds are placeholders).

### 7) Webhook verification (GET)
Expose the app (e.g., `ngrok http 8000`). Meta will call:
```
GET /webhook?hub.mode=subscribe&hub.verify_token=WHATSAPP_VERIFY_TOKEN&hub.challenge=1234
```
If the token matches, the endpoint echoes `hub.challenge`.

### 8) Signature verification (POST)
Real WA traffic includes `X-Hub-Signature-256`. We verify with `WHATSAPP_APP_SECRET`. For local mocks, omit the header or compute the correct HMAC of the raw body.

### 9) Optional: use Postgres locally
- Set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/waexpense`
- Ensure the DB exists; the app will auto-create tables on start (demo only—use Alembic later).

## Frontend: Run & Test
- Location: `frontend/nextjs-app`
- Install & run:
  ```
  cd frontend/nextjs-app
  npm install
  # optionally set NEXT_PUBLIC_API_BASE (defaults to http://127.0.0.1:8000)
  NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 npm run dev
  ```
- Access: http://localhost:3000 — page pulls from backend `/api/expenses` (currently dummy data).
- If your backend is not on `http://127.0.0.1:8000`, set an env in Next.js (e.g., `NEXT_PUBLIC_API_BASE=http://your-host:8000`) and use it in fetch calls once wired.

## Notes / Roadmap
- Tables auto-create on startup for now; switch to Alembic migrations for real use.
- OCR/image handling and background jobs are still stubbed.
- Keep secrets out of Git; prefer `.env` + secret managers in production.
