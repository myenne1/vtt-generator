from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    MAX_FILE_SIZE: int
    ALLOWED_EXTENSIONS: list[str]
    ALLOWED_MIME_TYPES: list[str]
    
    class Config:
        env_file = "./configurations/configs.env"
        env_file_encoding = "utf-8"

settings = Settings()