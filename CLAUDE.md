# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**TriageIQ** — an AI-powered customer support ticket triage & routing system (Quantic MSSE Capstone, solo developer).
It classifies incoming tickets by category + priority, routes them to the correct team, and (Sprint 3) suggests
resolutions via a RAG pipeline.

- **Backend** (this repo, `triageiq-api`): Python + FastAPI, deployed as a Vercel serverless function.
- **Frontend** (`triageiq-web`, separate repo): Next.js + shadcn/ui, deployed separately to Vercel.
- **LLM provider**: pluggable. Ollama locally (free/private); a hosted OpenAI-compatible API (Groq/OpenRouter) in prod.
- **Vector store**: Chroma (RAG). **DB**: SQLite (dev) → Postgres (prod). **CI**: GitHub Actions.

See `docs/PROJECT_BRIEF.md`, `docs/USER_STORIES.md`, and `README.md` for full context.

### Layout
- `app/main.py` — FastAPI entrypoint (`/health`, mounts routers, CORS).
- `app/config.py` — env-based settings (`pydantic-settings`).
- `app/models/` — Pydantic models + taxonomy (category/priority/team enums).
- `app/services/` — business logic: `classifier.py`, `llm_client.py` (provider abstraction + factory),
  `router.py` (rule-based routing), `repository.py` (DB access), `retriever.py` (pluggable RAG retrieval:
  TF-IDF prod / Chroma dev), `suggestion.py` (RAG resolution suggestions).
- `app/api/` — route definitions.
- `data/` — synthetic dataset generator + dataset + eval set.
- `tests/` — unit/integration tests (mock the model client; no network/key needed). `eval_classifier.py` is a
  manual script (needs a live model), not collected by pytest.

### Commands
- Run: `uvicorn app.main:app --reload`
- Tests: `pytest`
- Classifier accuracy eval (needs live Ollama): `python -m tests.eval_classifier`

## Commit messages

**Never include AI/LLM authorship attribution in commit messages.** Specifically:
- Do **not** add `Co-Authored-By: Claude ...`, `Generated with Claude Code`, or any line indicating the commit
  was written by an AI/LLM assistant.
- Do **not** mention Claude, Anthropic, or any AI tool as the author.

Technical terms that describe the actual product (e.g. "LLM client", "OpenAI-compatible provider") are fine — the
rule is about authorship attribution, not the domain vocabulary of this LLM-based system.

Write commit messages as if authored by the developer: concise subject line, body explaining the *why*.

## Linear (task board)

This repo is tracked in Linear — team **TriageIQ** (`TRI-*` issues), project **TriageIQ**. The Claude account is
integrated with Linear via MCP.

At the start of meaningful work, **reconcile the board with reality**:
1. Inspect the actual state of the codebase (what's implemented, tested, deployed).
2. For each `TRI-*` issue, move it to the status that matches reality:
   - **Done** — the work is implemented and covered by tests/CI where applicable.
   - **In Progress** — actively being worked on or partially landed.
   - **Todo / Backlog** — not started.
3. Don't mark an item Done unless the code actually exists and passes tests. Verify, don't assume.
4. When you start implementing a backlog item, move it to **In Progress**; when finished and verified, move it to **Done**.
5. Keep epics' status consistent with their children (an epic is Done only when its children are Done).

Statuses available: Backlog, Todo, In Progress, Done, Canceled, Duplicate.

## Working norms
- Sprint order: 1 (classification) → 2 (routing/persistence/dashboard/deploy) → 3 (RAG/hardening/docs).
- Keep tests green; add tests for new services. Mock the LLM client in unit tests.
- Don't commit secrets (`LLM_API_KEY`); `.env` is gitignored, `.env.example` documents config.
