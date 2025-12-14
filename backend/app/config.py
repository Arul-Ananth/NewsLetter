from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = "desktop-local-insecure-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./newsroom.db"

    # AI & External APIs
    SERPER_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = "NA"

    # Ollama / Local AI Config (These were missing!)
    OPENAI_API_BASE: str = "http://127.0.0.1:11434"
    OPENAI_MODEL_NAME: str = "ollama/mistral"

    class Config:
        env_file = ".env"
        # This tells Pydantic to ignore extra fields in .env file if we haven't defined them,
        # preventing the crash if you add comments or other junk to .env
        extra = "ignore"

settings = Settings()