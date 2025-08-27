from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    MONGO_URI: str = Field(...)
    DB_NAME: str = Field(...)
    SMTP_STARTTLS: bool = Field(default=True)
    DEFAULT_RESERVATION_LOCK_SECONDS: int = Field(default=30)
    DEFAULT_WORKER_BATCH_SIZE: int = Field(default=20)
    DISPATCHER_TICK_SECONDS: int = Field(default=15)
    DAY_BOUNDARY_TZ: str = Field(default="UTC")
    LOG_LEVEL: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
