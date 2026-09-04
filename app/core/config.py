from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Centralia Travel API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str
    DIRECT_URL: str = ""  # Alembic migratsiyalar uchun (bo'sh bo'lsa DATABASE_URL ishlatiladi)

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""
    PAYME_TEST_KEY: str = ""
    PAYME_ACCOUNT_FIELD: str = "booking_id"

    CLICK_SERVICE_ID: str = ""
    CLICK_MERCHANT_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    CLICK_MERCHANT_USER_ID: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    FRONTEND_SUCCESS_URL: str = "http://localhost:3000/booking/success"
    FRONTEND_CANCEL_URL: str = "http://localhost:3000/booking/cancel"

    MEDIA_ROOT: str = "media"
    MEDIA_URL: str = "/media/"

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "media"

    SUPPORTED_LANGUAGES: List[str] = ["uz", "ru", "en"]
    DEFAULT_LANGUAGE: str = "uz"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
