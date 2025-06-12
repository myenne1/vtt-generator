from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    MAX_FILE_SIZE: int
    ALLOWED_EXTENSIONS: list[str]
    ALLOWED_MIME_TYPES: list[str]
    BUCKET_NAME: str
    TIME_WINDOW: int
    MIME_CHECKING: bool
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None

    BUCKET_NAME: str
    
    class Config:
        env_file = "./configurations/configs.env"
        env_file_encoding = "utf-8"

settings = Settings()