"""
LLM client abstraction.

Design rationale (see docs/DESIGN_AND_TESTING.md for full discussion):
Local LLM hosting (Ollama) is free and keeps data private during development,
but free-tier deployment platforms (Render, Railway) cannot host a local model
with GPU requirements. By defining a minimal provider-agnostic interface here,
the rest of the application never depends on *how* completions are generated —
only on this `LLMClient` contract. This means the deployed environment can swap
to a different backend via configuration alone, with zero changes to
classification or RAG logic.
"""
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Minimal interface every LLM provider implementation must satisfy."""

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Generate a text completion for the given prompt."""
        raise NotImplementedError


class OllamaClient(LLMClient):
    """LLM client backed by a local Ollama instance."""

    def __init__(self, model: str, host: str):
        import ollama
        self._client = ollama.Client(host=host)
        self._model = model

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat(model=self._model, messages=messages)
        return response["message"]["content"]


def get_llm_client() -> LLMClient:
    """
    Factory function returning the configured LLM client.

    Adding a new provider later (e.g., a hosted API for production) means
    implementing LLMClient and adding one branch here — no other code changes.
    """
    from app.config import settings

    if settings.llm_provider == "ollama":
        return OllamaClient(model=settings.ollama_model, host=settings.ollama_host)

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
