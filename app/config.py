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

    # Hosted provider (used when llm_provider == "openai_compatible").
    # Defaults target Groq's free, fast endpoint; swap base_url + model for OpenRouter/OpenAI.
    #   Groq:        https://api.groq.com/openai/v1   model e.g. llama-3.1-8b-instant
    #   OpenRouter:  https://openrouter.ai/api/v1     model e.g. meta-llama/llama-3.1-8b-instruct:free
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.1-8b-instant"
    llm_api_key: str = ""  # set via LLM_API_KEY env / Vercel env var; never commit a real key

    # Database
    database_url: str = "sqlite:///./triageiq.db"

    # Vector store (RAG)
    chroma_persist_dir: str = "./chroma_db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
