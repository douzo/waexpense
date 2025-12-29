from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = Field(..., env="APP_NAME")
    debug: bool = Field(..., env="DEBUG")
    database_url: str = Field(..., env="DATABASE_URL")

    # WhatsApp Cloud API
    whatsapp_verify_token: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_app_secret: str = Field(..., env="WHATSAPP_APP_SECRET")
    whatsapp_access_token: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")

    # JWT / auth
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(..., env="JWT_ALGORITHM")
    access_token_expiry_minutes: int = Field(15, env="ACCESS_TOKEN_EXPIRY_MINUTES")
    refresh_token_expiry_days: int = Field(1, env="REFRESH_TOKEN_EXPIRY_DAYS")
    login_code_expiry_minutes: int = Field(10, env="LOGIN_CODE_EXPIRY_MINUTES")

    # Optional external text parser service (AWS/GCP, custom endpoint, etc.)
    external_text_parser_url: str = Field(..., env="EXTERNAL_TEXT_PARSER_URL")
    external_text_parser_api_key: Optional[str] = Field(
        default=None, env="EXTERNAL_TEXT_PARSER_API_KEY"
    )

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
