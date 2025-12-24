# WhatsApp Expense Tracker Architecture (MVP)

## Requirements & Status
- [x] FastAPI app scaffold with `/health` and `/webhook` routes.
- [x] Text message handling: parse free-form text, create expenses, send confirmation.
- [x] SQLAlchemy models: `users`, `expenses`, `receipts`.
- [x] WhatsApp client (signature verification + send message).
- [x] Serverless deployment path (API Gateway + Lambda + SQS + RDS).
- [x] Frontend dashboard: login + list expenses.
- [ ] Image handling: download media via WhatsApp Cloud API, store to S3, create `receipts` row, enqueue OCR job.
- [ ] OCR worker: consume queue, run OCR, update receipts/expenses, notify user.
- [ ] Alembic migrations and production DB hardening.

## Backend (Serverless FastAPI + Workers)
- **API Lambda (VPC)** runs FastAPI via Mangum for dashboard endpoints and auth.
- **Webhook Lambda (public)** receives WhatsApp callbacks and enqueues parsed payloads into SQS.
- **Worker Lambda (VPC)** consumes SQS and writes to RDS.
- **Outbound Lambda (public)** consumes outbound SQS messages and calls WhatsApp API.
- Text parsing prefers external parser (Bedrock-based Lambda via API Gateway) with regex fallback.

## Frontend (Next.js)
- Static export deployed to S3 (optionally behind CloudFront).
- Calls API Gateway endpoint (configured via `NEXT_PUBLIC_API_BASE`).

## Data Storage
- PostgreSQL (RDS) in private subnets.
- SQS queues for inbound/outbound message flow.
- S3 for static frontend and receipt storage (future image flow).

## Architecture Diagram
- Mermaid diagram: `docs/architecture.mmd`
- AWS icon diagram (PlantUML): `docs/architecture.puml`
