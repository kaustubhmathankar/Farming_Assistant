from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI Village Farming Assistant"
    app_env: str = "development"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v1"

    database_url: str

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-20b"
    vision_model: str = "qwen/qwen3.8-27b"
    stt_model: str = "whisper-large-v3-turbo"

    tavily_api_key: str = ""
    data_gov_api_key: str = ""

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "agriculture_knowledge"
    rag_chunk_size: int = 900
    rag_chunk_overlap: int = 150
    rag_top_k: int = 4
    rag_min_score: float = 0.0

    memory_message_limit: int = 12

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    login_rate_limit: str = "5/minute"
    register_rate_limit: str = "5/minute"
    agent_rate_limit: str = "30/minute"

    image_max_size_mb: int = 10
    audio_max_size_mb: int = 10
    request_timeout_seconds: int = 20

    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_hosts: str = "localhost,127.0.0.1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.allowed_origins.split(",") if x.strip()]

    @property
    def hosts(self) -> list[str]:
        return [x.strip() for x in self.allowed_hosts.split(",") if x.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    if not settings.jwt_secret_key:
        if settings.app_env.lower() == "production":
            raise RuntimeError("JWT_SECRET_KEY must be configured in production.")
        import secrets
        settings.jwt_secret_key = secrets.token_urlsafe(48)
    return settings


settings = get_settings()
