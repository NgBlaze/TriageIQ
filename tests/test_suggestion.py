"""
Unit tests for the RAG resolution-suggestion service.

The retriever and LLM are both stubbed so the service's logic (grounding,
no-match handling, source surfacing) is tested in isolation.
"""
from unittest.mock import patch

from app.models.ticket import ResolutionSuggestion
from app.services.retriever import RetrievedTicket
from app.services import suggestion as suggestion_mod
from app.services.suggestion import suggest_resolution


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def query(self, text, k):
        return self._hits[:k]


def _hit(id=1, score=0.5, category="billing"):
    return RetrievedTicket(
        id=id, subject="Charged twice", body="billed twice",
        category=category, resolution="Refunded the duplicate.", score=score,
    )


@patch.object(suggestion_mod, "get_llm_client")
@patch.object(suggestion_mod, "get_retriever")
def test_returns_grounded_suggestion_with_sources(mock_get_retriever, mock_get_llm):
    mock_get_retriever.return_value = FakeRetriever([_hit(1, 0.6), _hit(2, 0.3)])
    mock_get_llm.return_value.generate.return_value = "  Here is a suggested reply.  "

    result = suggest_resolution("Charged twice", "I was billed twice")

    assert isinstance(result, ResolutionSuggestion)
    assert result.has_match is True
    assert result.suggestion == "Here is a suggested reply."  # trimmed
    assert [s.id for s in result.sources] == [1, 2]


@patch.object(suggestion_mod, "get_llm_client")
@patch.object(suggestion_mod, "get_retriever")
def test_no_confident_match_declines_without_calling_llm(mock_get_retriever, mock_get_llm):
    # All hits below the default min score threshold.
    mock_get_retriever.return_value = FakeRetriever([_hit(1, 0.0), _hit(2, 0.001)])

    result = suggest_resolution("totally unrelated", "gibberish query")

    assert result.has_match is False
    assert result.suggestion is None
    assert result.sources == []
    assert result.note  # explains manual handling
    mock_get_llm.return_value.generate.assert_not_called()
