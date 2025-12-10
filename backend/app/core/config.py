from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field("WA Expense Tracker", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    whatsapp_verify_token: str = Field("change-me", env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_app_secret: str = Field("app-secret", env="WHATSAPP_APP_SECRET")
    whatsapp_access_token: str = Field("access-token", env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field("phone-number-id", env="WHATSAPP_PHONE_NUMBER_ID")


settings = Settings()
