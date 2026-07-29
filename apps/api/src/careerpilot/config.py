from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ENV_FILES = (
    str(_REPO_ROOT / ".env"),
    str(_REPO_ROOT / ".env.naukri"),
    ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "CareerPilot AI"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"

    database_url: str = (
        "postgresql+asyncpg://careerpilot:careerpilot_dev@localhost:5433/careerpilot"
    )
    redis_url: str = "redis://localhost:6379/0"

    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "careerpilot"
    storage_secret_key: str = "careerpilot_dev"
    storage_bucket: str = "careerpilot-resumes"
    storage_region: str = "us-east-1"
    resume_max_bytes: int = 10 * 1024 * 1024

    # AI resume extraction (OpenAI-compatible: OpenAI, LM Studio, DeepSeek, etc.)
    resume_ai_enabled: bool = False
    resume_ai_api_base: str = ""
    resume_ai_api_key: str = ""
    resume_ai_model: str = "gpt-4o-mini"
    resume_ai_timeout_seconds: float = 180.0
    resume_ai_max_chars: int = 60000
    resume_ai_max_tokens: int = 8192
    resume_ai_json_mode: bool = True
    # Prefer json_schema response_format when the provider supports it.
    # LM Studio (newer) accepts json_schema|text and rejects json_object.
    resume_ai_json_schema: bool = False
    # Second LLM pass — doubles latency; keep false for local/small models.
    resume_ai_verify_pass: bool = False
    resume_ai_fallback_heuristic: bool = True

    session_ttl_days: int = 30
    session_cookie_name: str = "careerpilot_session"
    session_cache_enabled: bool = True

    web_app_url: str = "http://localhost:3000"
    credentials_secret: str = "careerpilot-dev-credentials-secret-change-me"

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/v1/auth/linkedin/callback"
    linkedin_scopes: str = "openid profile email"
    # When true (or when client_id is empty in development), use local mock OAuth.
    linkedin_mock: bool = False

    # Naukri personal discovery (also loaded from .env.naukri)
    naukri_email: str = ""
    naukri_password: str = ""
    naukri_default_location: str = "Bengaluru"
    naukri_default_experience_years: int = 2
    naukri_default_skills: str = "Python,SQL"

    _LINKEDIN_PLACEHOLDER_IDS = frozenset(
        {"your_client_id", "your-client-id", "changeme", "replace_me", "xxx"}
    )
    _LINKEDIN_PLACEHOLDER_SECRETS = frozenset(
        {"your_client_secret", "your-client-secret", "changeme", "replace_me", "xxx"}
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    def _linkedin_client_id_effective(self) -> str:
        raw = self.linkedin_client_id.strip()
        if raw.lower() in self._LINKEDIN_PLACEHOLDER_IDS:
            return ""
        return raw

    def _linkedin_client_secret_effective(self) -> str:
        raw = self.linkedin_client_secret.strip()
        if raw.lower() in self._LINKEDIN_PLACEHOLDER_SECRETS:
            return ""
        return raw

    @property
    def linkedin_credentials_configured(self) -> bool:
        return bool(
            self._linkedin_client_id_effective() and self._linkedin_client_secret_effective()
        )

    @property
    def linkedin_enabled(self) -> bool:
        return self.linkedin_credentials_configured or self.linkedin_mock_enabled

    @property
    def linkedin_mock_enabled(self) -> bool:
        if self.linkedin_mock:
            return True
        return self.app_env == "development" and not self.linkedin_credentials_configured

    @property
    def linkedin_scope_list(self) -> list[str]:
        return [s.strip() for s in self.linkedin_scopes.split() if s.strip()]

    @property
    def naukri_configured(self) -> bool:
        return bool(self.naukri_email.strip() and self.naukri_password.strip())

    @property
    def sync_database_url(self) -> str:
        """Sync driver URL for Alembic migrations."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
