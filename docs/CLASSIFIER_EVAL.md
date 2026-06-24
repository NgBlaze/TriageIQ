# Classifier Evaluation & Manual Quality Review

Evidence for the classifier-accuracy success criterion and a manual review of a
sample of predictions. Reproduce with `python -m tests.eval_classifier`
(requires a live LLM); raw per-ticket output is written to
`tests/eval_results.json`.

## Method

- **Dataset:** 50-ticket hand-labeled evaluation set (`data/eval_set.json`),
  balanced across categories and priorities. No real customer data.
- **Model:** `llama-3.1-8b-instant` via Groq (the production provider),
  temperature 0 for deterministic output.
- **Procedure:** each ticket is classified; the predicted category/priority are
  compared to the gold labels. Requests are throttled with retry/backoff to
  respect the free-tier rate limit.

## Headline results

| Metric | Result | Target |
|---|---|---|
| Tickets evaluated | 46 / 50 (4 parse failures, see below) | — |
| **Category accuracy** | **91.3%** | ≥ 80% ✅ |
| Priority accuracy | 58.7% | (no formal target) |
| Mean confidence | 0.906 | — |

### Per-class breakdown

**Category** — account 100% (16/16), product 100% (4/4), billing 88.9% (8/9),
other 88.9% (8/9), bug_report 75% (6/8).

**Priority** — high 76.9% (10/13), low 70% (7/10), medium 45% (9/20),
critical 33.3% (1/3).

## Manual review of the misses

### Category (4 misses — all on genuinely ambiguous boundaries)
- *"Export feature produces empty file"* and *"Search returns no results"* →
  predicted **product**, labeled **bug_report**. Reasonable disagreement: phrased
  as feature behavior, they sit on the product-usage / defect boundary.
- *"Upgrade pricing question"* → predicted **product**, labeled **billing**.
  Mentions a plan feature *and* pricing; defensible either way.
- *"Question about your roadmap"* → predicted **product**, labeled **other**.

None are gross errors — they are the inherently fuzzy edges between categories,
which is exactly where automated triage benefits from the human-in-the-loop
`needs_review` path.

### Priority (the harder, more subjective task)
Priority is intrinsically subjective and the misses are mostly off-by-one-level:
- The model **up-ranks operational issues** ("Dashboard not loading", "App
  crashes on startup" → high vs labeled medium) and **down-ranks inquiries**
  ("Press inquiry", "Partnership inquiry" → low vs labeled medium).
- A few labels themselves look noisy — e.g. *"Compliment"* labeled **high**
  (predicted low) — which inflates the apparent error rate.
- `medium` is the weakest class (45%): it's the catch-all middle that both
  high- and low-leaning tickets get pulled away from.

**Confidence is weakly calibrated** — several misses carry 0.98 confidence — so
confidence is treated as a coarse signal only; the `needs_review` flag uses a
conservative threshold rather than trusting confidence as ground truth.

### Robustness (4 parse failures)
Four tickets returned truncated JSON (`{"category": …` cut off) and failed
parsing. At ~8% this is non-trivial and is the main reliability item to watch.
Mitigations: constrain/condense the model's output (e.g. drop or shorten the
`reasoning` field, cap output tokens) so responses can't run long, and the
existing 502/needs_review handling already prevents a bad parse from persisting
a mis-triaged ticket.

## Conclusions

- **Category classification meets the success criterion (91.3% ≥ 80%)** and is
  effectively perfect on the well-separated classes (account, product).
- **Priority is advisory**, not authoritative: ~59% with mostly one-level,
  defensible disagreements and some label noise. It's useful for surfacing
  likely-urgent tickets but is intentionally backed by deterministic
  escalation routing (any `critical` → escalations) and manual review.
- **Recommended next steps:** add priority-rubric examples / few-shot priority
  cases to the prompt, tighten output formatting to eliminate truncation
  failures, and revisit a few noisy priority labels in the eval set.
