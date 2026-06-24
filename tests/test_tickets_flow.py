"""
Integration tests for the full Sprint 2 triage flow: submit → classify → route
→ persist, plus listing/filtering the queue.

The LLM is mocked (deterministic, no network) and persistence runs against a
fresh in-memory SQLite database per test via a dependency override, so these
run fast and in CI with no external services.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.ticket import ClassificationResult, TicketCategory, TicketPriority

# Import to register the ORM model on Base.metadata before create_all.
# (use `from ... import` so the top-level `app` package name doesn't shadow the
# FastAPI `app` instance imported above)
from app.models import db_models  # noqa: F401


@pytest.fixture
def client():
    """TestClient backed by an isolated in-memory DB (shared across the test's
    connections via StaticPool)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_result(category=TicketCategory.BILLING, priority=TicketPriority.MEDIUM,
                 confidence=0.9, needs_review=False):
    return ClassificationResult(
        category=category, priority=priority, confidence=confidence,
        reasoning="r", needs_review=needs_review,
    )


@patch("app.api.tickets.classify_ticket")
def test_submit_classifies_routes_and_persists(mock_classify, client):
    mock_classify.return_value = _mock_result(TicketCategory.BILLING, TicketPriority.MEDIUM)

    resp = client.post(
        "/api/tickets",
        json={"subject": "Double charge", "body": "Charged twice this month."},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] >= 1
    assert data["category"] == "billing"
    assert data["routed_team"] == "billing_team"
    assert data["status"] == "routed"


@patch("app.api.tickets.classify_ticket")
def test_low_confidence_ticket_flagged_for_review(mock_classify, client):
    mock_classify.return_value = _mock_result(confidence=0.3, needs_review=True)

    resp = client.post("/api/tickets", json={"subject": "Vague request", "body": "not sure"})

    assert resp.status_code == 201
    data = resp.json()
    assert data["needs_review"] is True
    assert data["status"] == "needs_review"
    # And it surfaces as needs_review in the listed queue too.
    assert client.get("/api/tickets").json()[0]["needs_review"] is True


@patch("app.api.tickets.classify_ticket")
def test_critical_ticket_routed_to_escalations(mock_classify, client):
    mock_classify.return_value = _mock_result(TicketCategory.BUG_REPORT, TicketPriority.CRITICAL)

    resp = client.post("/api/tickets", json={"subject": "Outage", "body": "App down for all."})

    assert resp.status_code == 201
    assert resp.json()["routed_team"] == "escalations"


@patch("app.api.tickets.classify_ticket")
def test_submit_does_not_persist_on_classification_failure(mock_classify, client):
    mock_classify.side_effect = ValueError("LLM unreachable")

    resp = client.post("/api/tickets", json={"subject": "X", "body": "Y"})
    assert resp.status_code == 502

    # Nothing should have been persisted.
    assert client.get("/api/tickets").json() == []


@patch("app.api.tickets.classify_ticket")
def test_list_returns_newest_first_and_filters(mock_classify, client):
    mock_classify.return_value = _mock_result(TicketCategory.BILLING, TicketPriority.LOW)
    client.post("/api/tickets", json={"subject": "Billing q", "body": "b"})

    mock_classify.return_value = _mock_result(TicketCategory.BUG_REPORT, TicketPriority.HIGH)
    client.post("/api/tickets", json={"subject": "Bug", "body": "b"})

    all_tickets = client.get("/api/tickets").json()
    assert len(all_tickets) == 2
    # Newest first: the bug report was submitted last.
    assert all_tickets[0]["category"] == "bug_report"

    # Filter by team.
    eng = client.get("/api/tickets", params={"team": "engineering"}).json()
    assert len(eng) == 1
    assert eng[0]["routed_team"] == "engineering"

    # Filter by priority.
    high = client.get("/api/tickets", params={"priority": "high"}).json()
    assert len(high) == 1
    assert high[0]["priority"] == "high"
