"""
Integration tests for the ticket classification API endpoint.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.ticket import ClassificationResult, TicketCategory, TicketPriority

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
