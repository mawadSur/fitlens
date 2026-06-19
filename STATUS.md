# FitLens — Build Status

Legend: ✅ **live & tested** · 🟡 **scaffolded / interface-ready** (real code, needs wiring or data) · 🔴 **blocked on external accounts / ToS**

This is a **working vertical slice on the full PRD architecture**, not a finished 36-week platform. Nothing below is overstated.

## Core platform

| Component | Status | Notes |
|---|---|---|
| FastAPI backend + REST API | ✅ | Runs, OpenAPI docs at `/docs`, CORS configured |
| Domain model + DB | ✅ | SQLAlchemy; **SQLite in dev**, Postgres-ready via `DATABASE_URL` (🟡 real Postgres needs an instance) |
| Alembic migrations | ✅ | Baseline migration for all 9 tables; `alembic upgrade head` / `make migrate` |
| DB connection pooling | ✅ | `pool_size`/`max_overflow`/`pre_ping` auto-applied for non-SQLite URLs |
| Seed data | ✅ | 8 consultants across all visa types, 8 jobs, 4 vendors, rate cards |
| Embeddings + vector match | ✅ | Real ONNX `all-MiniLM-L6-v2` (384d); local cosine store |
| Pinecone / Weaviate / pgvector stores | 🟡 | Adapter code present (lazy-imported), credential/instance-gated |
| RBAC (5 roles) | ✅ | JWT bearer + `require_role` guards; enforcement off by default (`AUTH_ENFORCED`) |
| Observability | ✅ | Structured logging (JSON option) + request-ID tracing middleware |
| CI/CD | ✅ | GitHub Actions: API pytest + web tsc/build + Playwright e2e |
| Next.js frontend | ✅ | Dashboard, Hot Bench, consultant detail, Jobs, Submissions, Integrations |
| Unit + API tests | ✅ | 216 passing, deterministic (170 prior + 46 added for connectors, vector store, RBAC, observability, migrations). The generated tests surfaced 2 real bugs since fixed: a `visa_allows` USC/GC eligibility gap and a `_consultant_vector` bug that matched on the wrong resume. |
| E2E tests | ✅ | 5 Playwright specs through real Chrome, all passing |
| Chrome validation | ✅ | Every page screenshotted; submit + interview flows exercised live |
| Auth (Azure AD / Okta) | 🔴 | Config + provider switch present; SSO needs tenant/app registration |

## The 12 agents

| # | Agent | Status | What's real |
|---|---|---|---|
| 1 | Bench Monitoring | ✅ | Availability/bench-cost computation, alerts, hot-bench feed |
| 2 | Resume Intelligence | ✅ | Parse (PDF/DOCX/TXT), skill extraction, embedding; 🟡 LLM tailoring uses local fallback until an LLM key is set |
| 3 | Immigration Compliance | ✅ | Expiry alerts, transfer-eligibility rules per visa, job eligibility |
| 4 | Market Intelligence | 🟡 | Demand/rate from internal rate cards + job counts; 🔴 live Dice/LinkedIn market feeds need accounts |
| 5 | Job Matching | ✅ | Embeddings + skill/rate/visa scoring → match %, interview & placement probability |
| 6 | Vendor Relationship | ✅ | Composite vendor scoring + ranking |
| 7 | Marketing | 🟡 | Hotlist + email/LinkedIn copy via local LLM fallback; real copy needs an LLM key |
| 8 | Submission | ✅ | Rate selection, RTR generation, submission record + status |
| 9 | Follow-up | ✅ | Cadence (D1/3/5/7/14) + drafts; 🔴 actual send needs SMTP/Graph creds |
| 10 | Interview Coordinator | ✅ | Slot proposal + interview record + confirmation; 🔴 calendar push needs Outlook/Google/Teams |
| 11 | Placement Prediction | ✅ | Probability from match/vendor/demand/interview/bench signals |
| 12 | Revenue Forecast | ✅ | Expected placements, revenue, margin, bench burn |

> Agents 4/7 are marked 🟡 only because their *outputs* improve with a real LLM/market feed — the agent logic, contracts, and API endpoints are live now.

## Integrations (all credential-gated — flip to LIVE when creds are supplied)

| Connector | Status | Blocker |
|---|---|---|
| JobDiva | 🔴 | Customer JobDiva account (REST v2 client coded) |
| Bullhorn | 🔴 | Bullhorn OAuth2 account |
| Ceipal | 🔴 | Ceipal account |
| Dice | 🔴 | Partner/API feed — ⚠️ scraping violates ToS |
| Indeed | 🔴 | Publisher ID |
| Monster | 🔴 | Employer API access |
| LinkedIn | 🔴 | Talent Solutions partner — ⚠️ scraping violates ToS |
| Email (SMTP) | 🟡 | Real SMTP creds (full send path coded) |
| Teams (Graph) | 🔴 | Azure app registration |

## Remaining for true production (the 70–80% beyond this slice)

Legend below: ✅ scaffolding landed this session · ⬜ still needs external accounts / infra.

1. **Real data plane** — ✅ Alembic migrations + connection pooling + pgvector adapter landed. ⬜ Still needs a provisioned Postgres instance with the `pgvector` extension.
2. **Real integrations** — ✅ `_fetch_live` bodies coded for all 🔴 job-source connectors + Teams Graph send (credential-gated, parsing unit-tested offline). ⬜ Still needs customer ATS/job-board accounts to run end-to-end, plus ingestion pipelines + dedupe.
3. **Autonomy** — ⬜ schedule the agents (n8n / Celery / a job scheduler), human-in-the-loop approvals, audit log.
4. **AuthZ/RBAC** — ✅ 5 PRD roles + JWT + `require_role` guards landed (enforcement-gated). ⬜ Still needs SSO tenant registration and per-tenant isolation (multi-tenant SaaS).
5. **Security & compliance** — ⬜ PII handling for immigration docs, encryption at rest, SOC2 posture.
6. **LLM quality** — ⬜ wire a real provider for resume tailoring / marketing / follow-up copy; eval harness.
7. **Observability + deploy** — ✅ structured logging + request-ID tracing + CI (GitHub Actions) landed. ⬜ Still needs metrics/distributed tracing exporters and Azure/AWS infra-as-code.
8. **Scale-out matching** — ✅ pgvector/Weaviate ANN adapters wired behind `VECTOR_PROVIDER`. ⬜ Still needs the index provisioned + provider switched as the corpus grows.
