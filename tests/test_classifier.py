"""
Unit tests for the classification service.

These tests mock the LLM client entirely so they run fast, deterministically,
and without requiring a live Ollama instance — suitable for CI. Accuracy
against real model output is measured separately via tests/eval_classifier.py,
which is a deliberately distinct concern from "does the parsing/plumbing work."
"""
import json
from unittest.mock import patch

import pytest

from app.models.ticket import TicketCategory, TicketPriority
from app.services.classifier import classify_ticket, _parse_llm_response


def make_fake_response(category="billing", priority="medium", confidence=0.9, reasoning="test"):
    return json.dumps({
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "reasoning": reasoning,
    })


class TestParseLLMResponse:
    def test_parses_clean_json(self):
        raw = make_fake_response()
        parsed = _parse_llm_response(raw)
        assert parsed["category"] == "billing"
        assert parsed["priority"] == "medium"

    def test_parses_json_with_surrounding_text(self):
        raw = f"Here is my answer: {make_fake_response()} Hope that helps!"
        parsed = _parse_llm_response(raw)
        assert parsed["category"] == "billing"

    def test_raises_on_no_json_found(self):
        with pytest.raises(ValueError):
            _parse_llm_response("I'm not sure how to classify this.")


class TestClassifyTicket:
    @patch("app.services.classifier.get_llm_client")
    def test_classify_returns_valid_result(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.generate.return_value = make_fake_response(
            category="bug_report", priority="critical", confidence=0.95
        )

        result = classify_ticket("App crashes", "It crashes on every launch.")

        assert result.category == TicketCategory.BUG_REPORT
        assert result.priority == TicketPriority.CRITICAL
        assert result.confidence == 0.95

    @patch("app.services.classifier.get_llm_client")
    def test_classify_raises_on_invalid_category(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.generate.return_value = make_fake_response(category="not_a_real_category")

        with pytest.raises(ValueError):
            classify_ticket("Test subject", "Test body")

    @patch("app.services.classifier.get_llm_client")
    def test_classify_raises_on_malformed_response(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.generate.return_value = "not json at all"

        with pytest.raises(ValueError):
            classify_ticket("Test subject", "Test body")
