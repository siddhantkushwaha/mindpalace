from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class VectorStoreSettings(BaseSettings):
    host: str = "localhost"
    port: int = 8000
    collection: str = "mindpalace"


class EmbeddingSettings(BaseSettings):
    model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    batch_size: int = 64


class LLMSettings(BaseSettings):
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str | None = None
    fallback_model: str | None = None
    temperature: float = 0.3
    max_tokens: int = 2048


class RAGSettings(BaseSettings):
    top_k: int = 10
    rerank_top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 64


class DatabaseSettings(BaseSettings):
    url: str = "postgresql://mindpalace:mindpalace@localhost:5432/mindpalace"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    auth_secret: str = ""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)


settings = Settings()
