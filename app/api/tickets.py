"""
Sprint 1 API routes: ticket submission and classification.

Routing and persistence are deliberately out of scope here and land in
Sprint 2 — this endpoint demonstrates the core classification capability
in isolation.
"""
from fastapi import APIRouter, HTTPException

from app.models.ticket import TicketCreate, ClassificationResult
from app.services.classifier import classify_ticket

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("/classify", response_model=ClassificationResult)
def classify(ticket: TicketCreate) -> ClassificationResult:
    """
    Classify a ticket's category and priority without persisting it.

    Sprint 1 scope: classification only. Sprint 2 adds persistence + routing.
    """
    try:
        return classify_ticket(subject=ticket.subject, body=ticket.body)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Classification failed: {exc}",
        ) from exc
