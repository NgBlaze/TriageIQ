# TriageIQ

**AI-Powered Customer Support Ticket Triage & Routing System**

MSSE Capstone Project — Quantic School of Business and Technology

## Overview

TriageIQ automatically classifies incoming customer support tickets by category and priority, routes them to the correct team, and suggests resolutions based on similar past tickets using a Retrieval-Augmented Generation (RAG) pipeline.

See [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) for full project context and [`docs/DESIGN_AND_TESTING.md`](docs/DESIGN_AND_TESTING.md) for architecture and testing documentation (added progressively across sprints).

## Features

- 🤖 **LLM-based classification** — category (Billing/Product/Account/Bug Report/Other) + priority (Critical/High/Medium/Low)
- 🔀 **Automated routing** — tickets routed to the correct team queue based on classification
- 📚 **RAG-powered resolution suggestions** — retrieves similar resolved tickets and drafts a suggested response
- 📊 **Dashboard** — submit tickets and view the triaged queue

## Tech Stack

- **Backend**: Python, FastAPI (this repo) — deployed as a Vercel serverless function
- **LLM**: pluggable client — **Ollama** locally (free/private); **Groq or OpenRouter** (free, OpenAI-compatible) in production
- **Vector store**: Chroma (for RAG retrieval)
- **Database**: SQLite (dev) / PostgreSQL (deployed, e.g. Neon/Supabase free tier)
- **Frontend**: Next.js + shadcn/ui — **separate repo** (`triageiq-web`), also on Vercel
- **Deployment**: Vercel (free tier) — frontend and backend as two projects
- **CI/CD**: GitHub Actions

> **Repos:** the system is split into two repositories — `triageiq-api` (this one, FastAPI backend) and `triageiq-web` (Next.js frontend). Both deploy independently to Vercel and are shared with `quantic-grader`.

## Project Structure

```
triageiq/
├── app/
│   ├── main.py              # FastAPI app entrypoint (+ DB schema init on startup)
│   ├── db.py                 # SQLAlchemy engine/session (SQLite dev → Postgres prod)
│   ├── models/               # Pydantic API models + SQLAlchemy ORM models
│   ├── services/             # Business logic (classification, routing, persistence, RAG)
│   ├── api/                  # API route definitions
│   └── config.py             # App configuration / env settings
├── data/
│   ├── synthetic_tickets.json    # Generated synthetic ticket dataset
│   └── eval_set.json             # Hand-labeled evaluation set
├── tests/                    # Unit & integration tests
├── docs/
│   ├── PROJECT_BRIEF.md
│   ├── DESIGN_AND_TESTING.md
│   └── USER_STORIES.md
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed locally with a model pulled (e.g., `ollama pull llama3.1`)

### Setup
```bash
# Clone the repo
git clone <repo-url>
cd triageiq

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (dev set includes Ollama, Chroma, and test tooling)
pip install -r requirements-dev.txt

# Run the app
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/tickets/classify` | Classify a ticket (category + priority), no persistence |
| `POST` | `/api/tickets` | Full triage: classify → route to team queue → persist |
| `GET` | `/api/tickets` | List the triaged queue; filter by `team` and/or `priority` |

Routing is deterministic: any `critical` ticket goes to **escalations**; otherwise the ticket routes by category (billing→billing_team, product→product_team, account→account_support, bug_report→engineering, other→general_support).

### Running Tests
```bash
pytest
```

## Deployment (Vercel)

The backend deploys to Vercel as a Python serverless function. `api/index.py`
re-exports the FastAPI app and `vercel.json` routes all requests to it; the same
app object runs locally and in production.

**Steps:**
1. Import this repo as a Vercel project (root directory = repo root). Vercel
   detects `vercel.json` and installs `requirements.txt` (prod-lean).
2. Provision a free Postgres database (e.g. [Neon](https://neon.tech)) — Vercel's
   filesystem is ephemeral, so SQLite won't persist.
3. Set the project's Environment Variables in Vercel:

   | Variable | Value |
   |---|---|
   | `LLM_PROVIDER` | `openai_compatible` |
   | `LLM_BASE_URL` | `https://api.groq.com/openai/v1` (or OpenRouter) |
   | `LLM_MODEL` | `llama-3.1-8b-instant` (or an OpenRouter model) |
   | `LLM_API_KEY` | your Groq / OpenRouter key |
   | `DATABASE_URL` | the Postgres connection string (`postgres://…` is auto-normalized) |
   | `CORS_ORIGINS` | the deployed frontend URL, e.g. `https://triageiq-web.vercel.app` |

4. Deploy. Verify `GET /health` on the deployed URL, then exercise
   `POST /api/tickets` and `GET /api/tickets`.

> Note: `chromadb` (RAG, Sprint 3) is intentionally **not** in the prod bundle yet
> — it's in `requirements-dev.txt`. Revisit `requirements.txt` when RAG ships to deployment.

## Sprint Plan

| Sprint | Focus |
|---|---|
| 1 | Synthetic data generation + baseline LLM classifier |
| 2 | Routing logic, persistence, dashboard UI, deployment |
| 3 | RAG-based resolution suggestions, hardening, final testing/docs |

## License

Academic project — Quantic School of Business and Technology MSSE Capstone.
