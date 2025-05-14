# backend/app/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Skyent API"
    admin_email: str = "admin@skyent.dev"
    items_per_user: int = 50
    log_level: str = "INFO"

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./skyent.db"
    async_database_url: Optional[str] = None
    db_echo: bool = True  # Set to False in production
    test_database: bool = False

    # Pool configuration
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # 30 minutes
    
    # Tavily API configuration
    tavily_api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
