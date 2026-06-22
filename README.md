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

- **Backend**: Python, FastAPI
- **LLM**: Ollama (local, open-source models) — pluggable client architecture
- **Vector store**: Chroma (for RAG retrieval)
- **Database**: SQLite (dev) / PostgreSQL (deployed)
- **Frontend**: React (or lightweight server-rendered UI)
- **Deployment**: Render (free tier)
- **CI/CD**: GitHub Actions

## Project Structure

```
triageiq/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── models/               # Pydantic models & DB schema
│   ├── services/             # Business logic (classification, routing, RAG)
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

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Running Tests
```bash
pytest
```

## Sprint Plan

| Sprint | Focus |
|---|---|
| 1 | Synthetic data generation + baseline LLM classifier |
| 2 | Routing logic, persistence, dashboard UI, deployment |
| 3 | RAG-based resolution suggestions, hardening, final testing/docs |

## License

Academic project — Quantic School of Business and Technology MSSE Capstone.
