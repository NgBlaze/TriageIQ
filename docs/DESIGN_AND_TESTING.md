# TriageIQ — Design & Testing Document

MSSE Capstone — Quantic School of Business and Technology

This document records the architecture and design decisions behind TriageIQ, the
patterns used and why, the testing approach and results, and the deployment
option chosen with its cost implications. It complements
[`PROJECT_BRIEF.md`](PROJECT_BRIEF.md) (problem/scope) and
[`USER_STORIES.md`](USER_STORIES.md) (backlog).

---

## 1. System Overview

TriageIQ automates customer-support ticket triage end-to-end:

1. **Classify** — an LLM assigns a category (billing / product / account /
   bug_report / other) and priority (critical / high / medium / low).
2. **Route** — deterministic rules map the classification to a team queue.
3. **Persist** — the triaged ticket is stored and exposed as a queue.
4. **Suggest** — a RAG pipeline retrieves similar resolved tickets and drafts a
   grounded resolution suggestion.

The system is split into two independently deployed repositories:
**`triageiq-api`** (this repo — FastAPI backend) and **`triageiq-web`**
(Next.js frontend). Both deploy to Vercel free tier.

---

## 2. Architecture & Patterns

### 2.1 Layered architecture

```
HTTP (FastAPI routers)        app/api/tickets.py
        │
Domain services               app/services/{classifier,router,suggestion}.py
        │
Provider abstractions         app/services/{llm_client,retriever}.py
        │
Persistence (repository)      app/services/repository.py  ← app/models/db_models.py
        │
Config (env)                  app/config.py
```

Each layer depends only on the one below it. Routers stay thin (validate →
delegate → serialize); business logic lives in services; data access is isolated
in the repository. This keeps the code testable (each layer mocked in isolation)
and makes the storage and model providers swappable without touching endpoints.

### 2.2 Patterns used

| Pattern | Where | Why |
|---|---|---|
| **Strategy / provider abstraction** | `LLMClient` (Ollama vs OpenAI-compatible), `Retriever` (TF-IDF vs Chroma) | Decouple application logic from *how* completions/retrieval happen, so dev and prod can use different backends via config alone — no code changes. |
| **Factory** | `get_llm_client()`, `get_retriever()` | A single place selects the concrete implementation from configuration; adding a provider is one new branch. |
| **Repository** | `services/repository.py` | Isolates SQLAlchemy queries from endpoints; the DB can change (SQLite → Postgres) without touching callers. |
| **Dependency Injection** | FastAPI `Depends(get_db)` | Request-scoped DB sessions; tests override the dependency with an in-memory DB. |
| **Singleton (process-scoped)** | cached retriever | The corpus is loaded/indexed once per process (idempotent "ingestion"), amortized across requests including serverless warm invocations. |
| **DTO separation** | Pydantic API models vs SQLAlchemy ORM models | API contract (validation/serialization) is decoupled from the DB schema. |

### 2.3 Key design decisions

- **Prompt-based classification (not fine-tuning).** A few-shot prompt with a
  strict JSON output contract avoids needing a labeled training set and a
  training pipeline, and keeps the model swappable. Output is parsed
  defensively (regex-extract the JSON object) to tolerate minor model noise.
- **Deterministic routing (no LLM).** `(category, priority) → queue` is pure,
  auditable, and free: any `critical` ticket escalates; otherwise it routes by
  category. A misroute is a fixable rule bug, not model nondeterminism.
- **Pluggable LLM provider.** Ollama locally (free, private, no key); a hosted
  OpenAI-compatible API (Groq/OpenRouter) in production, because Vercel's
  serverless runtime can't host a local GPU model. One `OpenAICompatibleClient`
  covers all OpenAI-compatible providers.
- **Pluggable retriever.** Chroma + embeddings for local development (the
  "vector store" story); a pure-python **TF-IDF** retriever as the production
  default, because Chroma's dependencies (onnxruntime) risk Vercel's 250 MB
  function limit and its persistent store can't survive an ephemeral filesystem.
  Both sit behind one `Retriever` interface.
- **Grounded RAG with a decline path.** The suggestion prompt forbids outside
  knowledge; when no sufficiently similar past ticket is found (or the topic
  isn't covered), the service returns `has_match=false` / a fixed "handle
  manually" message rather than hallucinating.
- **Low-confidence flagging.** Classifications with confidence ≤
  `CONFIDENCE_THRESHOLD` set `needs_review` and status `needs_review`, so
  uncertain predictions surface for a human instead of silently mis-routing.
  `needs_review` is **derived** from the stored confidence at read time, which
  avoided a production schema migration.

---

## 3. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/tickets/classify` | Classify only (no persistence) |
| `POST` | `/api/tickets` | Full triage: classify → route → persist |
| `GET` | `/api/tickets` | Queue, filterable by `team` / `priority` |
| `POST` | `/api/tickets/suggest` | RAG resolution suggestion + source tickets |

Failure handling: a classification/suggestion LLM failure returns **502** and
nothing is persisted; invalid/blank input returns **422**; all LLM calls are
bounded by `LLM_TIMEOUT` (default 30 s).

---

## 4. Testing Approach & Results

### 4.1 Strategy

Tests are split by concern and the LLM is always mocked in automated tests, so
the suite is fast, deterministic, and runs in CI with no network or API key.

| Layer | File | What it covers |
|---|---|---|
| Classifier unit | `tests/test_classifier.py` | JSON parsing (clean, noisy, missing), enum mapping |
| LLM client unit | `tests/test_llm_client.py` | OpenAI-compatible request/response, API-key guard, URL handling |
| Routing unit | `tests/test_router.py` | Every category route + critical-escalation rule + string coercion |
| Retriever unit | `tests/test_retriever.py` | TF-IDF ranking, top-k, zero-score for unrelated queries |
| Suggestion unit | `tests/test_suggestion.py` | Grounded suggestion + sources; no-match declines without calling the LLM |
| API integration | `tests/test_api.py` | classify/suggest endpoints, validation (422), LLM failure (502) |
| Flow integration | `tests/test_tickets_flow.py` | submit → classify → route → persist over an in-memory DB; filters; low-confidence flag; no-persist-on-failure |

**Result: 39 automated tests passing.** CI (`.github/workflows/ci.yml`) runs the
full suite on every push and PR.

### 4.2 Evaluation harnesses (manual, need a live LLM)

- **Classifier accuracy** — `tests/eval_classifier.py` scores predictions
  against the 50-ticket hand-labeled set (`data/eval_set.json`), reporting
  category and priority accuracy. Used to evidence the ≥80% success criterion.
- **RAG qualitative eval** — `tests/eval_rag.py` runs representative probes
  (including an out-of-domain case) through the full suggestion pipeline and
  prints retrieved sources + scores + the generated suggestion for grounding
  review.

### 4.3 Live deployment verification (observed)

Against the deployed URL:
- `/health` → `{"status":"ok"}`.
- `POST /api/tickets` (duplicate-charge ticket) → classified `billing`/`medium`
  (confidence 0.98), routed to `billing_team`, persisted to Postgres.
- `POST /api/tickets/suggest` (locked-out ticket) → retrieved the password-reset
  resolution (similarity 0.74) and drafted a grounded suggestion; an off-domain
  probe correctly declined; blank input returned 422.

### 4.4 RAG tuning notes

TF-IDF similarity scores observed: strong matches ~0.5–0.74, secondary/weak
matches ~0.18–0.36. Because a borderline off-domain query can score ~0.27 (not
cleanly separable from real secondary matches by threshold alone), grounding is
enforced primarily at the **prompt** level — the model is instructed to decline
and never use outside knowledge — with the score threshold as a coarse first
gate. `RAG_TOP_K` (default 3) balances enough grounding context against prompt
noise.

---

## 5. Deployment Options & Cost Tradeoffs

### 5.1 Chosen: Vercel (serverless) + Neon Postgres + Groq

| Component | Choice | Free-tier cost |
|---|---|---|
| Backend host | Vercel Python serverless function | $0 |
| Frontend host | Vercel (separate project) | $0 |
| Database | Neon Postgres | $0 |
| LLM (prod) | Groq (OpenAI-compatible) | $0 |
| LLM (dev) | Ollama (local) | $0 |
| Retrieval (prod) | in-process TF-IDF | $0 |
| CI | GitHub Actions | $0 |

**Total running cost: $0**, satisfying the Capstone free-tier guidance.

### 5.2 Serverless constraints that shaped the design

- **Ephemeral filesystem** → SQLite wouldn't persist between invocations, so
  production uses Postgres (`DATABASE_URL`); a `postgres://` URL is auto-
  normalized to `postgresql://`.
- **~250 MB function bundle limit** → `chromadb`/`ollama` are dev-only
  (`requirements-dev.txt`); the prod bundle is lean and uses the dependency-free
  TF-IDF retriever. The RAG corpus JSON is kept in the bundle via `.vercelignore`.
- **No GPU / can't host a local model** → the hosted OpenAI-compatible provider
  is used in prod, selected purely by env config.

### 5.3 Alternatives considered

- **Render (original plan)** — viable and offers managed Postgres, but a free
  web service sleeps on idle (cold starts) and the project already standardized
  on Vercel for the frontend; one platform simplifies ops.
- **Chroma + hosted embeddings in prod** — most faithful to the original
  "vector DB" plan but adds bundle weight, an external embedding dependency, and
  cold-start re-ingestion. Deferred in favor of the serverless-safe TF-IDF path
  behind the same interface, so it can be swapped back if needed.

---

## 6. Limitations & Future Work

- **Synthetic data only** — no real customer data is used; classifier/RAG
  quality is demonstrated on curated synthetic sets.
- **TF-IDF retrieval in prod** is lexical, not semantic; the `chroma` backend
  (semantic embeddings) exists behind the same interface for environments
  without serverless size constraints.
- **No auth** — single-user/demo scope by design.
- **Schema migrations** use `create_all` (additive); a production system would
  adopt Alembic.
- Future: native confidence visualization and analytics in the dashboard,
  semantic retrieval in prod, and integration with a real ticketing platform.
