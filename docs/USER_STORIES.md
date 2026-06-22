# TriageIQ — User Stories & Backlog

Organized by epic and sprint. Each story follows the standard format:
**As a [role], I want [capability], so that [benefit].**

Priority: 🔴 Must-have for sprint | 🟡 Should-have | 🟢 Nice-to-have / stretch

---

## Epic 1: Synthetic Data & Baseline Classification (Sprint 1)

| # | User Story | Priority |
|---|---|---|
| 1.1 | As the Product Owner, I want a synthetic dataset of realistic support tickets, so that I can develop and test the classifier without using real customer data. | 🔴 |
| 1.2 | As the Product Owner, I want a hand-labeled evaluation subset, so that I can objectively measure classifier accuracy. | 🔴 |
| 1.3 | As a developer, I want a pluggable LLM client interface, so that the system isn't locked to one provider and can support different environments (local dev vs. deployed). | 🔴 |
| 1.4 | As a developer, I want an Ollama-backed LLM client implementation, so that classification works against a free, local model during development. | 🔴 |
| 1.5 | As a support agent, I want to submit a ticket's subject and body and receive a predicted category, so that I don't have to manually categorize it. | 🔴 |
| 1.6 | As a support agent, I want the system to also predict a priority level, so that urgent tickets can be identified automatically. | 🔴 |
| 1.7 | As the Product Owner, I want an evaluation script that reports classifier accuracy against the labeled set, so that classifier quality is measurable and improvable. | 🔴 |
| 1.8 | As a developer, I want unit tests covering the classification service and parsing logic, so that regressions are caught automatically. | 🔴 |
| 1.9 | As a developer, I want a CI pipeline that runs tests on every push, so that code quality is enforced continuously. | 🟡 |

**Sprint 1 demo goal:** Submit a ticket via API → receive a JSON classification (category + priority + confidence).

---

## Epic 2: Routing, Persistence & Dashboard (Sprint 2)

| # | User Story | Priority |
|---|---|---|
| 2.1 | As a support agent, I want classified tickets automatically routed to the correct team queue, so that they reach the right people without manual handoff. | 🔴 |
| 2.2 | As a team lead, I want tickets persisted in a database, so that ticket history isn't lost between sessions. | 🔴 |
| 2.3 | As a support agent, I want a web form to submit a new ticket, so that I don't need to use the raw API. | 🔴 |
| 2.4 | As a team lead, I want a dashboard showing all tickets with their category, priority, and assigned team, so that I have visibility into the current queue. | 🔴 |
| 2.5 | As a team lead, I want to filter the dashboard by team or priority, so that I can focus on the most urgent items first. | 🟡 |
| 2.6 | As the Product Owner, I want the application deployed to a publicly accessible URL, so that it can be demonstrated and used outside of local development. | 🔴 |
| 2.7 | As a developer, I want integration tests covering the full submit → classify → route → persist flow, so that the end-to-end pipeline is verified. | 🔴 |

**Sprint 2 demo goal:** Submit a ticket via the web UI → see it classified, routed, and appear in a live dashboard on the deployed URL.

---

## Epic 3: RAG-Based Resolution Suggestions & Hardening (Sprint 3)

| # | User Story | Priority |
|---|---|---|
| 3.1 | As the Product Owner, I want a small corpus of synthetic resolved tickets with their resolutions, so that the system has historical data to retrieve from. | 🔴 |
| 3.2 | As a developer, I want resolved tickets embedded and stored in a vector database, so that similar tickets can be retrieved efficiently. | 🔴 |
| 3.3 | As a support agent, I want a suggested resolution generated for each new ticket based on similar past tickets, so that I have a head start on responding. | 🔴 |
| 3.4 | As a support agent, I want to see which past tickets a suggestion was based on, so that I can verify the suggestion's relevance before using it. | 🟡 |
| 3.5 | As the Product Owner, I want low-confidence classifications flagged for manual review, so that uncertain predictions don't silently mis-route a ticket. | 🟡 |
| 3.6 | As a developer, I want edge cases (empty fields, ambiguous tickets, LLM failures) handled gracefully, so that the system doesn't crash on unexpected input. | 🔴 |
| 3.7 | As the Product Owner, I want a finalized design and testing document, so that architecture decisions and test coverage are clearly recorded for submission. | 🔴 |
| 3.8 | As the Product Owner, I want a recorded demonstration of the complete system, so that the working product can be presented and submitted. | 🔴 |

**Sprint 3 demo goal:** Full flow including an AI-generated, retrieval-grounded resolution suggestion shown alongside each routed ticket.

---

## Backlog (Not Yet Scheduled / Stretch Goals)

| # | User Story | Priority |
|---|---|---|
| B.1 | As a team lead, I want classifier confidence visualized in the dashboard, so that I can spot tickets needing manual double-checking at a glance. | 🟢 |
| B.2 | As a developer, I want to compare prompt-based classification against a fine-tuned model, so that I can evaluate whether fine-tuning meaningfully improves accuracy. | 🟢 |
| B.3 | As a team lead, I want basic analytics (ticket volume by category/priority over time), so that I can identify trends. | 🟢 |
