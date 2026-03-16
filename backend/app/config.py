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
    ai_provider: str = "groq"  # "groq" or "anthropic"
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    ai_model: str = "llama-3.3-70b-versatile"  # groq default
    ai_model_fast: str = "llama-3.1-8b-instant"  # groq fast

    # Auth
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
