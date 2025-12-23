"""Shared configuration for server and desktop."""
import os
import sys
from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMode(str, Enum):
    SERVER = "SERVER"
    DESKTOP = "DESKTOP"


class Settings(BaseSettings):
    # Core
    APP_MODE: AppMode = AppMode.SERVER
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI / External Services
    OPENAI_API_BASE: str = "http://localhost:11434/v1/openai"
    OPENAI_MODEL_NAME: str = "mistral:latest"
    SERPER_API_KEY: str = ""  # Optional

    # Data Storage
    DATA_DIR: Path = Path("./data")

    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[2] / ".env"), extra="ignore")

    def configure(self) -> None:
        """Set DATA_DIR based on APP_MODE and ensure it exists."""
        if self.APP_MODE == AppMode.DESKTOP:
            if sys.platform == "win32":
                appdata = os.environ.get("APPDATA")
                base_dir = Path(appdata) / "AeroBrief" if appdata else Path.home() / "AppData" / "Roaming" / "AeroBrief"
            else:
                base_dir = Path.home() / ".local" / "share" / "AeroBrief"
            self.DATA_DIR = base_dir

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.configure()
