"""
Repository / data-access layer for tickets.

Isolates SQLAlchemy queries from the API and service code: callers ask for
"create this ticket" or "list the queue" and never build queries themselves.
This keeps the DB swappable and the endpoints thin, and gives tests a single
seam to exercise persistence.
"""
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import TicketORM


def create_ticket(
    db: Session,
    *,
    subject: str,
    body: str,
    customer_email: str | None,
    category: str | None,
    priority: str | None,
    confidence: float | None,
    routed_team: str | None,
    status: str = "routed",
) -> TicketORM:
    """Persist a triaged ticket and return the stored row (with its id)."""
    ticket = TicketORM(
        subject=subject,
        body=body,
        customer_email=customer_email,
        category=category,
        priority=priority,
        confidence=confidence,
        routed_team=routed_team,
        status=status,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def list_tickets(
    db: Session,
    *,
    team: str | None = None,
    priority: str | None = None,
) -> Sequence[TicketORM]:
    """Return tickets newest-first, optionally filtered by team and/or priority."""
    stmt = select(TicketORM)
    if team:
        stmt = stmt.where(TicketORM.routed_team == team)
    if priority:
        stmt = stmt.where(TicketORM.priority == priority)
    stmt = stmt.order_by(TicketORM.created_at.desc(), TicketORM.id.desc())
    return db.execute(stmt).scalars().all()
