# FitLens — Workforce Supply Intelligence

Agentic Bench Sales Operating System (BSOS) for staffing firms running H1B / OPT / GC / USC / C2C / W2 consultants. This repo is a **working vertical slice** of the PRD built on the PRD stack (FastAPI + Next.js + SQLAlchemy + ONNX embeddings), with all 12 agents present and the bench → match → submit → interview loop fully functional, tested, and Chrome-validated.

See **[STATUS.md](./STATUS.md)** for the precise ✅ live / 🟡 scaffolded / 🔴 blocked status of every PRD component.

## Architecture

```
apps/
  api/                      FastAPI backend (Python 3.13)
    app/
      models.py             SQLAlchemy domain model (consultants, jobs, vendors, submissions, immigration, users…)
      scoring.py            Pure scoring engine (match %, interview/placement probability) — unit-tested
      parsing.py            Resume text + skill extraction (PDF/DOCX/TXT)
      auth.py               5-role RBAC (admin/account-mgr/recruiter/bench-sales/viewer), JWT, role guards
      observability.py      Structured logging (JSON option) + request-ID tracing middleware
      embeddings/           ONNX all-MiniLM-L6-v2 (fastembed) + local/Pinecone/Weaviate/pgvector store
      llm/                  OpenAI/Anthropic/Gemini providers + deterministic local fallback
      connectors/           JobDiva/Bullhorn/Ceipal/Dice/Indeed/Monster/LinkedIn/Email/Teams (live paths, credential-gated)
      agents/               The 12 agents (talent / matching / outreach / analytics)
      routers/              REST API (+ /api/auth)
    alembic/                Database migrations (baseline for all 9 tables)
    tests/                  pytest — 216 passing
  web/                      Next.js 15 + TypeScript + Tailwind
    app/                    Dashboard, Hot Bench, consultant detail, Jobs, Submissions, Integrations
    e2e/                    Playwright (system Chrome)
.github/workflows/ci.yml    CI: API pytest + web tsc/build + Playwright e2e
Makefile                    make install / test / api / web / migrate / e2e
```

## Run it

**Backend** (port 8000):
```bash
cd apps/api
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000     # auto-seeds demo data on first boot
```

Dev boot calls `create_all` for zero-config startup. For a real database, manage schema with Alembic instead:
```bash
cd apps/api && .venv/bin/alembic upgrade head    # or: make migrate
```

**Frontend** (port 3000):
```bash
cd apps/web
npm install
API_BASE=http://localhost:8000 npm run dev
```
Open http://localhost:3000.

## Test

```bash
cd apps/api && .venv/bin/python -m pytest        # 216 unit + API integration tests
cd apps/web && npx playwright test               # e2e through real Chrome
make test                                        # api pytest + web tsc, from repo root
```

CI runs the same checks on every push/PR (`.github/workflows/ci.yml`).

## Auth (RBAC)

Five roles (`admin`, `account_manager`, `recruiter`, `bench_sales`, `viewer`) with JWT bearer tokens and `require_role` guards. Enforcement is **off by default** (`AUTH_ENFORCED=false`) so the demo runs open; set it to `true` to lock routes down. In dev, mint a token without SSO:

```bash
curl -sX POST localhost:8000/api/auth/token -H 'content-type: application/json' \
  -d '{"email":"me@firm.com","role":"recruiter"}'
# → {"access_token":"…","token_type":"bearer","role":"recruiter"}
```

Production SSO (Azure AD / Okta) plugs in via `AUTH_PROVIDER` — see `.env.example`.

## Going to production

Everything runs key-free in dev. To activate real services, copy `.env.example` → `.env` and fill in:
- `DATABASE_URL` → PostgreSQL (connection pooling kicks in automatically for non-SQLite URLs; manage schema with `alembic upgrade head`)
- `VECTOR_PROVIDER=pgvector|pinecone|weaviate` + the matching credentials (adapters are wired; local cosine is the default)
- `LLM_PROVIDER` + provider key
- `AUTH_ENFORCED=true` + `AUTH_PROVIDER=azuread|okta` to turn on RBAC enforcement and SSO
- ATS / job-board / comms credentials (each connector flips from MOCK to LIVE automatically once its keys are present)

Connector live/mock status is visible in-app on the **Integrations** page.

The platform scaffolding for production is in place: Alembic migrations, DB pooling, pgvector/Weaviate adapters, JWT RBAC, structured logging + request-ID tracing, and CI. The remaining 🔴 items in [STATUS.md](./STATUS.md) are blocked only on **external accounts** (ATS/job-board/SSO tenants) — the code paths exist and are credential-gated, but cannot be exercised end-to-end without those accounts.
