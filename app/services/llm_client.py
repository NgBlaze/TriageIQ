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
    """LLM client backed by a local Ollama instance (development default)."""

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


class OpenAICompatibleClient(LLMClient):
    """
    LLM client for any OpenAI-compatible chat-completions API.

    A single implementation covers Groq, OpenRouter, OpenAI, Together, etc. —
    they all expose the same `POST {base_url}/chat/completions` contract. The
    provider is selected purely by configuration (base URL + model + key), so
    production can run on a free hosted provider (Groq / OpenRouter) while dev
    stays on local Ollama, with no application-logic changes.

    Used for deployment because Vercel's serverless runtime cannot host a local
    GPU model the way Ollama does locally.
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30.0):
        if not api_key:
            raise ValueError(
                "LLM API key is not set. Provide LLM_API_KEY (e.g. a Groq or "
                "OpenRouter key) when using the openai_compatible provider."
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def generate(self, prompt: str, system: str | None = None) -> str:
        import httpx

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": messages,
                "temperature": 0,  # deterministic classification
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def get_llm_client() -> LLMClient:
    """
    Factory function returning the configured LLM client.

    Adding a new provider means implementing LLMClient and adding one branch
    here — no other code changes anywhere in the app.
    """
    from app.config import settings

    if settings.llm_provider == "ollama":
        return OllamaClient(model=settings.ollama_model, host=settings.ollama_host)

    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
