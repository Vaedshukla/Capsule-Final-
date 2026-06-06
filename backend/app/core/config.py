from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    # ─── Application ─────────────────────────────────────────────
    PROJECT_NAME: str = "Project Capsule"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True

    # ─── PostgreSQL ───────────────────────────────────────────────
    POSTGRES_USER: str = "capsule_user"
    POSTGRES_PASSWORD: str = "capsule_password"
    POSTGRES_DB: str = "capsule_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    # ─── Local-First Security ─────────────────────────────────────
    # Simple shared secret between extension and backend.
    # Empty string = development mode (no auth check performed).
    # Set a real value in .env for any non-development use.
    CAPSULE_API_KEY: str = ""

    # When True, backend rejects requests not originating from localhost.
    LOCALHOST_ONLY: bool = True

    # ─── Embeddings ───────────────────────────────────────────────
    # "local"  → sentence-transformers (offline, private, 384 dims)
    # "openai" → text-embedding-3-small (requires OPENAI_API_KEY, 1536 dims)
    EMBEDDING_PROVIDER: Literal["local", "openai"] = "local"
    EMBEDDING_MODEL_LOCAL: str = "all-MiniLM-L6-v2"
    EMBEDDING_MODEL_OPENAI: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 384

    # ─── Retrieval / Ranking Weights ─────────────────────────────
    # Composite rank = α·similarity + β·importance + γ·recency + δ·access
    RANK_WEIGHT_SIMILARITY: float = 0.45
    RANK_WEIGHT_IMPORTANCE: float = 0.25
    RANK_WEIGHT_RECENCY: float = 0.20
    RANK_WEIGHT_ACCESS: float = 0.10
    RANK_RECENCY_HALF_LIFE_DAYS: float = 30.0  # days before recency score halves

    # ─── Context Assembly ─────────────────────────────────────────
    CONTEXT_TOKEN_BUDGET: int = 2000        # max tokens for assembled context
    CONTEXT_DEDUP_THRESHOLD: float = 0.92  # cosine sim above this = duplicate

    # ─── Chunking ────────────────────────────────────────────────
    CHUNK_TARGET_TOKENS: int = 200    # target tokens per chunk
    CHUNK_OVERLAP_TOKENS: int = 40    # overlap between adjacent chunks

    # ─── AI Provider (optional — for future compression) ─────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ─── CORS ────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "chrome-extension://",
        "moz-extension://",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.development", ".env.production"),
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def async_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_uri(self) -> str:
        """Used by Alembic migrations (synchronous driver)."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
