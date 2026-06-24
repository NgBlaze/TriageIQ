"""
Application configuration.

LLM provider is configurable via environment variable so the app can run
against a local Ollama instance during development (zero cost, full
privacy) and swap to a different provider for deployment if needed,
without changing any application logic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TriageIQ"

    # LLM configuration
    #   "ollama"             -> local dev (free, private, no key)
    #   "openai_compatible"  -> any hosted OpenAI-compatible API (Groq, OpenRouter, OpenAI...)
    llm_provider: str = "ollama"
    ollama_model: str = "llama3.1"
    ollama_host: str = "http://localhost:11434"

    # Seconds to wait on any LLM call before failing (applies to all providers).
    llm_timeout: float = 30.0

    # Classifications at or below this confidence are flagged for manual review
    # so uncertain predictions don't silently mis-route a ticket.
    confidence_threshold: float = 0.5

    # Hosted provider (used when llm_provider == "openai_compatible").
    # Defaults target Groq's free, fast endpoint; swap base_url + model for OpenRouter/OpenAI.
    #   Groq:        https://api.groq.com/openai/v1   model e.g. llama-3.1-8b-instant
    #   OpenRouter:  https://openrouter.ai/api/v1     model e.g. meta-llama/llama-3.1-8b-instruct:free
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.1-8b-instant"
    llm_api_key: str = ""  # set via LLM_API_KEY env / Vercel env var; never commit a real key

    # Database
    database_url: str = "sqlite:///./triageiq.db"

    # CORS — comma-separated list of allowed frontend origins.
    # Dev default covers the local Next.js dev server; set CORS_ORIGINS in
    # production to the deployed frontend URL (e.g. https://triageiq-web.vercel.app).
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- RAG / resolution suggestions ---
    # Retriever backend, selected like the LLM provider:
    #   "tfidf"  -> pure-python TF-IDF cosine; zero deps, serverless-safe (prod default)
    #   "chroma" -> Chroma vector store + embeddings (local dev / design-doc story)
    retriever: str = "tfidf"
    rag_corpus_path: str = "data/resolved_tickets.json"
    rag_top_k: int = 3
    # Minimum similarity score for a retrieved ticket to count as a confident
    # match; below this the suggestion service declines rather than guess.
    rag_min_score: float = 0.05

    # Vector store (RAG, used when retriever == "chroma")
    chroma_persist_dir: str = "./chroma_db"
    embedding_model: str = "nomic-embed-text"  # Ollama embedding model for dev

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
