"""
Ticket API routes.

- POST /api/tickets/classify : classify only, no persistence (Sprint 1 demo slice).
- POST /api/tickets          : full triage — classify, route, persist (Sprint 2).
- GET  /api/tickets          : list the persisted queue, with optional filters.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.ticket import (
    ClassificationResult,
    TeamQueue,
    TicketCreate,
    TicketPriority,
    TicketRead,
)
from app.services import repository
from app.services.classifier import classify_ticket
from app.services.router import route_ticket

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("/classify", response_model=ClassificationResult)
def classify(ticket: TicketCreate) -> ClassificationResult:
    """
    Classify a ticket's category and priority without persisting it.

    Retained from Sprint 1 as a lightweight, side-effect-free classification
    probe. Use POST /api/tickets for the full triage flow.
    """
    try:
        return classify_ticket(subject=ticket.subject, body=ticket.body)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Classification failed: {exc}",
        ) from exc


@router.post("", response_model=TicketRead, status_code=201)
def submit_ticket(ticket: TicketCreate, db: Session = Depends(get_db)) -> TicketRead:
    """
    Full triage: classify the ticket, route it to a team queue, and persist it.

    This is the end-to-end Sprint 2 flow (submit → classify → route → persist)
    backing the dashboard. A classification failure returns 502 and nothing is
    persisted, so the queue never contains un-triaged rows.
    """
    try:
        result = classify_ticket(subject=ticket.subject, body=ticket.body)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Classification failed: {exc}",
        ) from exc

    routed_team = route_ticket(result.category, result.priority)

    stored = repository.create_ticket(
        db,
        subject=ticket.subject,
        body=ticket.body,
        customer_email=ticket.customer_email,
        category=result.category.value,
        priority=result.priority.value,
        confidence=result.confidence,
        routed_team=routed_team.value,
        status="routed",
    )
    return TicketRead.model_validate(stored)


@router.get("", response_model=list[TicketRead])
def list_queue(
    db: Session = Depends(get_db),
    team: Optional[TeamQueue] = Query(default=None, description="Filter by routed team queue"),
    priority: Optional[TicketPriority] = Query(default=None, description="Filter by priority"),
) -> list[TicketRead]:
    """
    Return the triaged ticket queue (newest first), optionally filtered by team
    and/or priority — backs the dashboard and its filters.
    """
    rows = repository.list_tickets(
        db,
        team=team.value if team else None,
        priority=priority.value if priority else None,
    )
    return [TicketRead.model_validate(row) for row in rows]
