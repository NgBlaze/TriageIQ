# Methodology & Agile Process

**Draft** — records the software-engineering methodology followed for TriageIQ
and an explicit solo-developer note (Handbook pp. 6–7; rubric: "appropriate
methodology"). Items marked _[fill in]_ need your actual dates before final
submission.

## Methodology: Scrum-style agile, adapted for a solo developer

TriageIQ was built with an iterative, sprint-based agile approach over three
sprints, each producing an independently demoable increment:

| Sprint | Focus | Increment / demo |
|---|---|---|
| 1 | Synthetic data + baseline LLM classifier | Submit ticket text → category + priority (JSON) |
| 2 | Routing, persistence, dashboard, deployment | Submit → classify → route → view, live on a public URL |
| 3 | RAG resolution suggestions, hardening, docs | Full flow incl. an AI-suggested, retrieval-grounded resolution |

Work is tracked on a **Linear** board (team `TRI`), organized as epics →
user stories → tasks, with statuses (Backlog → Todo → In Progress → Done) kept
current as work completed. The board was set up on **2026-06-22** and is the
single source of truth for scope and progress.

## Solo-developer note

This is a **solo project**: one person holds all roles (Product Owner,
Scrum Master, Developer). Ceremonies are therefore adapted rather than run as
multi-person meetings:

- **Sprint planning** is a self-directed session that selects the sprint's user
  stories from the backlog and breaks them into tasks on the board.
- **Daily stand-up** is replaced by a lightweight personal check-in (review the
  In-Progress column, note blockers) given the compressed timeline.
- **Sprint review/demo** is a recorded walkthrough submitted to the Product
  Owner at each sprint's end.
- **Retrospective** is a short written note of what to improve next sprint.

There is no GitHub branch-protection/review gate because there are no other
contributors; quality is enforced instead by **automated CI** (GitHub Actions
runs the full test suite on every push) and a documented test strategy
(see [`DESIGN_AND_TESTING.md`](DESIGN_AND_TESTING.md)).

## Ceremony log (evidence)

| Event | Date | Notes |
|---|---|---|
| Project / board set-up | 2026-06-22 | Linear board, epics, and backlog created |
| Sprint 1 planning | _[fill in]_ | Selected Epic 1 stories |
| Sprint 1 review + retro | _[fill in]_ | Demo recorded for Product Owner (TRI-89) |
| Sprint 2 planning | _[fill in]_ | Selected Epic 2 stories |
| Sprint 2 review + retro | _[fill in]_ | Demo recorded (TRI-90) |
| Sprint 3 planning | _[fill in]_ | Selected Epic 3 stories |
| Sprint 3 review + retro | _[fill in]_ | Demo recorded (TRI-91) |
| Final submission | _[fill in]_ | Repo, deployed link, board, docs, video |

> Development activity (per git history) ran from the baseline through
> **2026-06-24**. Replace the _[fill in]_ cells with the actual planning/review
> dates and a one-line retro note per sprint.

## Engineering practices applied

- **Version control & traceability** — Git history with focused commits;
  Linear issues map to the work (each issue carries a suggested branch name).
- **CI/CD** — GitHub Actions runs tests on every push/PR; the app
  auto-deploys to Vercel on push to `main`.
- **Testing** — unit + integration tests (LLM mocked) plus manual evaluation
  harnesses; results recorded in [`CLASSIFIER_EVAL.md`](CLASSIFIER_EVAL.md) and
  [`DESIGN_AND_TESTING.md`](DESIGN_AND_TESTING.md).
- **Incremental delivery** — each sprint ends with a working, deployable
  increment rather than a big-bang integration.
- **Documentation-as-deliverable** — project brief, user stories, design &
  testing doc, and this methodology note maintained alongside the code.
