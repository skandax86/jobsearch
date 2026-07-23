from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "CareerPilot AI"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://careerpilot:careerpilot_dev@localhost:5432/careerpilot"
    redis_url: str = "redis://localhost:6379/0"

    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "careerpilot"
    storage_secret_key: str = "careerpilot_dev"
    storage_bucket: str = "careerpilot-resumes"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


settings = Settings()
