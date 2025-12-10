from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field("WA Expense Tracker", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    whatsapp_verify_token: str = Field("change-me", env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_app_secret: str = Field("app-secret", env="WHATSAPP_APP_SECRET")
    whatsapp_access_token: str = Field("EAAVZCaga63ZB0BQEwRnJZAZBkRKi4AYrc5eiUuNdqZCExFnvonxN8i4El8fXGAjB9ddewCZBt3IxohUL0w4UQU5ujE7pBtwPjZAOZCuBpLGh64jVm0zPE9idcPXE1H3HuNOinfDvhn4pazTJPEbrriJ5ybw9W0NvhInmwcmftZBygtiW3R4BWmi3ZBeZAOk5imMdxKWvPsY8QvtVh4eUFkVNnc435LeLBRVOC0ZAn5W6OnXVPVzPeZBLyPZByLYhhL3WQCutfi6zk1EjrBXKFfRgSZA9orqamaSm7vBKVsFuakpegZDZD", env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field("936770472849383", env="WHATSAPP_PHONE_NUMBER_ID")


settings = Settings()
