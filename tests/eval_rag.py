"""
Qualitative evaluation of the RAG resolution-suggestion pipeline.

Runs a set of representative probe tickets through the suggestion service and
prints, for each, the retrieved source tickets (with similarity scores) and the
generated suggestion — so the output can be reviewed for relevance and grounding
and cited in the Design & Testing Document. Includes deliberate edge cases
(an out-of-domain query) to confirm the no-match path behaves.

This is a manual script (not collected by pytest): it needs a live LLM.
Run with: python -m tests.eval_rag
"""
from app.services.suggestion import suggest_resolution

PROBES = [
    ("Double billing", "I was charged twice for my subscription this month and want the duplicate refunded."),
    ("Locked out of account", "My password reset email never arrives and I can't log in."),
    ("App won't start", "After the latest update the application crashes the moment I open it."),
    ("Export is empty", "When I export my report to CSV the file downloads but it's completely empty."),
    ("Nonprofit pricing", "We're a registered nonprofit — do you offer any discount?"),
    ("Out of domain", "What's the weather like on Mars today and can you book me a flight?"),
]


def main() -> None:
    for subject, body in PROBES:
        print("=" * 80)
        print(f"TICKET: {subject}\n  {body}")
        result = suggest_resolution(subject, body)
        if not result.has_match:
            print(f"  -> NO CONFIDENT MATCH: {result.note}")
            continue
        print("  Sources:")
        for s in result.sources:
            print(f"    #{s.id} [{s.category}] score={s.score}  {s.subject}")
        print(f"  Suggestion:\n    {result.suggestion}")
    print("=" * 80)


if __name__ == "__main__":
    main()
