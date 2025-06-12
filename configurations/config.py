from pydantic_settings import BaseSettings

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
    OPENAI_API_KEY: str | None = None
    API_KEY: str
    RATE_LIMIT: str

    BUCKET_NAME: str
    TIME_WINDOW: int
    MIME_CHECKING: bool
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
