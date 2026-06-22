"""
Unit tests for the LLM client abstraction — specifically the hosted
OpenAI-compatible provider used in deployment (Groq / OpenRouter / OpenAI).

The HTTP call is mocked so these run in CI with no network and no API key.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_client import OpenAICompatibleClient, get_llm_client


def test_requires_api_key():
    with pytest.raises(ValueError):
        OpenAICompatibleClient(base_url="https://x/v1", api_key="", model="m")


@patch("httpx.post")
def test_generate_calls_chat_completions_and_returns_content(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "hello world"}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = OpenAICompatibleClient(
        base_url="https://api.groq.com/openai/v1/",  # trailing slash should be trimmed
        api_key="test-key",
        model="llama-3.1-8b-instant",
    )
    result = client.generate(prompt="classify this", system="you are a classifier")

    assert result == "hello world"

    called_url = mock_post.call_args.args[0]
    assert called_url == "https://api.groq.com/openai/v1/chat/completions"

    payload = mock_post.call_args.kwargs["json"]
    assert payload["model"] == "llama-3.1-8b-instant"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "classify this"

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer test-key"


def test_factory_unknown_provider_raises():
    with patch("app.config.settings") as mock_settings:
        mock_settings.llm_provider = "nope"
        with pytest.raises(ValueError):
            get_llm_client()
