"""
Seed the database with a sample of triaged tickets for demo/dashboard purposes.

Reuses the predictions already produced by the classifier eval
(`tests/eval_results.json`) joined with the ticket bodies in the labeled set,
so seeding makes NO new LLM calls — it just routes each prediction and persists
it via the normal repository path. Targets whatever DATABASE_URL points at
(local SQLite by default; Neon Postgres in the deployed/.env config).

Run with: python -m data.seed_tickets [N]   (default N=20)
"""
import json
import sys

from app.config import settings
from app.db import SessionLocal, init_db
from app.models.ticket import TicketCategory, TicketPriority
from app.services import repository
from app.services.router import route_ticket

EVAL_RESULTS = "tests/eval_results.json"
EVAL_SET = "data/eval_set.json"


def main(n: int = 20) -> None:
    init_db()
    results = json.load(open(EVAL_RESULTS))["results"]
    bodies = {t["id"]: t["body"] for t in json.load(open(EVAL_SET))}

    db = SessionLocal()
    created = 0
    try:
        for r in results[:n]:
            category = TicketCategory(r["predicted_category"])
            priority = TicketPriority(r["predicted_priority"])
            team = route_ticket(category, priority)
            needs_review = r["confidence"] <= settings.confidence_threshold
            repository.create_ticket(
                db,
                subject=r["subject"],
                body=bodies.get(r["id"], r["subject"]),
                customer_email=None,
                category=category.value,
                priority=priority.value,
                confidence=r["confidence"],
                routed_team=team.value,
                status="needs_review" if needs_review else "routed",
            )
            created += 1
    finally:
        db.close()
    print(f"Seeded {created} tickets into {settings.database_url.split('@')[-1] or settings.database_url}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
