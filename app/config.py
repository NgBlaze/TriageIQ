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
    llm_provider: str = "ollama"  # "ollama" | future: "openai", "anthropic", etc.
    ollama_model: str = "llama3.1"
    ollama_host: str = "http://localhost:11434"

    # Database
    database_url: str = "sqlite:///./triageiq.db"

    # Vector store (RAG)
    chroma_persist_dir: str = "./chroma_db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
