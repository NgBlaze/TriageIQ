"""
Integration tests for the ticket classification API endpoint.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.ticket import (
    ClassificationResult,
    ResolutionSuggestion,
    SuggestionSource,
    TicketCategory,
    TicketPriority,
)

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.api.tickets.classify_ticket")
def test_classify_endpoint_success(mock_classify):
    mock_classify.return_value = ClassificationResult(
        category=TicketCategory.ACCOUNT,
        priority=TicketPriority.HIGH,
        confidence=0.9,
        reasoning="test reasoning",
    )

    response = client.post(
        "/api/tickets/classify",
        json={"subject": "Can't log in", "body": "Password reset isn't working."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "account"
    assert data["priority"] == "high"


def test_classify_endpoint_rejects_empty_subject():
    response = client.post(
        "/api/tickets/classify",
        json={"subject": "", "body": "Some body text."},
    )
    assert response.status_code == 422  # Pydantic validation error


@patch("app.api.tickets.classify_ticket")
def test_classify_endpoint_handles_llm_failure(mock_classify):
    mock_classify.side_effect = ValueError("LLM unreachable")

    response = client.post(
        "/api/tickets/classify",
        json={"subject": "Test", "body": "Test body"},
    )

    assert response.status_code == 502


@patch("app.api.tickets.suggest_resolution")
def test_suggest_endpoint_returns_suggestion_and_sources(mock_suggest):
    mock_suggest.return_value = ResolutionSuggestion(
        has_match=True,
        suggestion="Refund the duplicate charge.",
        sources=[SuggestionSource(id=1, subject="Charged twice",
                                  category=TicketCategory.BILLING, score=0.6)],
    )

    response = client.post(
        "/api/tickets/suggest",
        json={"subject": "Charged twice", "body": "I was billed twice."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_match"] is True
    assert data["suggestion"] == "Refund the duplicate charge."
    assert data["sources"][0]["id"] == 1


@patch("app.api.tickets.suggest_resolution")
def test_suggest_endpoint_handles_no_match(mock_suggest):
    mock_suggest.return_value = ResolutionSuggestion(
        has_match=False, suggestion=None, sources=[], note="Needs manual handling."
    )

    response = client.post(
        "/api/tickets/suggest",
        json={"subject": "Odd one", "body": "Nothing similar."},
    )

    assert response.status_code == 200
    assert response.json()["has_match"] is False
