from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Tabot"
    environment: str = "development"
    secret_key: str = "change-me-in-production"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://tabot:tabot@localhost:5435/tabot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Meta / WhatsApp
    meta_verify_token: str = ""
    meta_app_secret: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""

    # Meta / Instagram
    instagram_account_id: str = ""

    # AI
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-4-20250514"
    ai_model_fast: str = "claude-haiku-4-5-20251001"

    # Auth
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
