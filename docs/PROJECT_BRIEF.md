# Project Brief: TriageIQ

**An AI-Powered Customer Support Ticket Triage & Routing System**

MSSE Capstone Project — Quantic School of Business and Technology
Track: AI System | Team size: Solo

---

## 1. Problem Statement

Customer support teams receive a high volume of incoming tickets that must be manually read, categorized, prioritized, and routed to the correct team before any actual resolution work can begin. This triage step is repetitive, time-consuming, and inconsistent — different agents may categorize similar tickets differently, and urgent tickets can sit in a queue if no one has reviewed them yet.

This is a real, recurring pain point in software/IT-adjacent support operations: manual classification doesn't scale, delays response time on critical issues, and pulls skilled staff away from actual problem-solving.

## 2. Proposed Solution

**TriageIQ** is an AI system that automates the ticket triage workflow end-to-end:

1. **Classification** — incoming tickets (subject + body) are automatically classified into a support category (Billing, Product, Account, Bug Report, Other) and assigned a priority level (Critical, High, Medium, Low) using an LLM-based classifier.
2. **Routing** — based on category and priority, tickets are automatically routed to the appropriate team queue.
3. **Resolution Assistance** — using a Retrieval-Augmented Generation (RAG) approach, the system retrieves similar previously-resolved tickets and drafts a suggested resolution for the assigned agent to review and use.

The system is designed so a support agent or team lead can submit a ticket and immediately see it classified, routed, and accompanied by a suggested next step — replacing manual triage with an assisted, AI-augmented workflow.

## 3. Why This Project

- **Real-world relevance**: ticket triage is a common operational bottleneck in tech/IT support contexts; this directly reflects a recurring problem in my own work environment.
- **Clear AI engineering scope**: combines prompt-based LLM classification with a RAG pipeline — both core AI engineering techniques covered in the MSSE program.
- **Measurable success criteria**: classification accuracy can be evaluated against a labeled test set, giving the project a rigorous, demonstrable evaluation story rather than subjective "it seems to work" claims.
- **Naturally incremental**: the system breaks cleanly into three sprint-sized increments (classification → routing/persistence/UI → RAG resolution suggestions), each independently demoable.

## 4. Target Users

- Support agents who currently triage tickets manually
- Team leads who need visibility into ticket volume, category, and priority across the queue
- (Conceptually) End customers, whose tickets get routed and resolved faster as a downstream benefit

## 5. Core User Value

> "As a support agent, I no longer need to manually read and categorize every incoming ticket — the system does it for me, routes it correctly, and gives me a head start on resolution."

## 6. Scope

### In Scope
- Synthetic ticket dataset generation (no real customer data used)
- LLM-based ticket classification (category + priority)
- Rule-based routing logic from classification → team queue
- Web-based dashboard for ticket submission and queue visibility
- RAG-based resolution suggestion using a corpus of synthetic resolved tickets
- Deployment of the application to a free-tier hosting environment
- Automated testing (classifier evaluation against labeled set, API tests, basic CI pipeline)

### Out of Scope
- Real customer/company data (handled via fully synthetic data per Capstone guidance)
- Fine-tuning a custom model (prompt-based classification only, per current scope)
- Multi-language ticket support
- Authentication/user account management (single-user/demo-oriented system)
- Integration with a real ticketing platform (e.g., Zendesk, Jira Service Desk) — though the architecture is designed to make this a feasible future extension

## 7. Technical Approach (Summary)

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python + FastAPI | Async-friendly for LLM calls; auto-generated API docs |
| LLM (dev) | Ollama (local, open-source models) | Zero cost, full data privacy, no rate limits during development |
| LLM (prod, if needed) | Pluggable client interface; swappable to a hosted provider | Local LLM hosting isn't viable on free-tier deployment platforms; architecture decouples LLM provider from application logic |
| Vector store (RAG) | Chroma | Free, embeddable, no infrastructure overhead |
| Database | SQLite (dev) → PostgreSQL (deployed) | Render provides free-tier Postgres |
| Frontend | Lightweight React or server-rendered HTML | Functional dashboard; submission form + queue view |
| Deployment | Render (free tier) | Matches Capstone deployment guidance |
| CI/CD | GitHub Actions | Automated test runs on push, satisfies CI/CD requirement |
| Task Board | Linear | Tracks epics/user stories/tasks across sprints |

A full justification of these choices — including architecture patterns used and deployment cost tradeoffs — will be documented in the Design & Testing Document required for final submission.

## 8. Success Criteria

- Classifier achieves a defined minimum accuracy (e.g., ≥80%) against a hand-labeled evaluation set
- End-to-end flow (submit → classify → route → display) works reliably in the deployed environment
- RAG resolution suggestions are coherent and grounded in retrieved historical tickets (evaluated qualitatively against a test set of sample tickets)
- All Capstone deliverable requirements satisfied: GitHub repo, deployed link, task board, design & testing document, recorded demonstration

## 9. Sprint Plan Overview

| Sprint | Focus | Key Demo |
|---|---|---|
| 1 | Synthetic data + baseline LLM classifier | Submit ticket text → receive category + priority |
| 2 | Routing logic, persistence, dashboard UI, deployment | Full submit → classify → route → view in dashboard, live on deployed URL |
| 3 | RAG-based resolution suggestions, hardening, testing/docs | Full flow including AI-suggested resolution |

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Synthetic data isn't realistic enough to produce meaningful classification results | Use an LLM to help generate varied, realistic ticket text across categories; manually review a sample for quality |
| Local LLM (Ollama) too slow/inconsistent for live demo | Pre-test demo flow ahead of recording; keep classification prompts concise; fall back to a hosted provider if needed for the recorded demo |
| RAG resolution suggestions are low quality or generic | Curate a focused, well-labeled corpus of resolved tickets; tune retrieval top-k and prompt structure iteratively in Sprint 3 |
| Scope creep (solo developer, fixed timeline) | Strict adherence to 3-sprint plan; "nice-to-have" extensions (e.g., fine-tuning) deferred unless time permits |
