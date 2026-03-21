"""Shared configuration for server and desktop."""
import os
import sys
from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMode(str, Enum):
    SERVER = "SERVER"
    DESKTOP = "DESKTOP"


class AuthMode(str, Enum):
    TRUSTED_LAN = "trusted_lan"
    INTERACTIVE = "interactive"


class Settings(BaseSettings):
    # Core
    APP_MODE: AppMode = AppMode.SERVER
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173"
    TRUSTED_LAN_MODE: bool = True
    AUTH_MODE: AuthMode | None = None
    TRUSTED_LAN_USER_EMAIL: str = "local@lan"
    TRUSTED_LAN_USER_NAME: str = "Trusted LAN User"
    AUTH_SESSION_EXPIRE_MINUTES: int = 720

    # AI / External Services
    LLM_PROVIDER: str | None = None
    OPENAI_API_BASE: str = ""
    OPENAI_MODEL_NAME: str = "mistral:latest"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    SERPER_API_KEY: str = ""  # Optional

    # Data Storage
    DATA_DIR: Path = Path("./data")

    # Desktop Data Collection
    DATA_COLLECTION_ENABLED: bool = True
    CLIPBOARD_COLLECTION_ENABLED: bool = False
    CLIPBOARD_STORE_RAW_TEXT: bool = False
    FOLDER_WATCH_ENABLED: bool = False
    MIN_CLIPBOARD_CHARS: int = 20
    DOC_MAX_MB: int = 10
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200
    QDRANT_COLLECTION_USER_DOCS: str = "user_documents"
    QDRANT_COLLECTION_SESSION_MEMORY: str = "session_memory"
    QDRANT_COLLECTION_USER_PROFILE: str = "user_profile"
    RETENTION_DAYS_EVENTS_RAW: int = 14
    EVENT_QUEUE_MAX: int = 500
    DEDUPE_WINDOW_SECONDS: int = 120
    PROFILE_ROLLUP_EVERY: int = 5

    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[2] / ".env"), extra="ignore")

    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]

    def auth_mode(self) -> AuthMode:
        if self.APP_MODE == AppMode.DESKTOP:
            return AuthMode.TRUSTED_LAN
        if self.AUTH_MODE is not None:
            return self.AUTH_MODE
        return AuthMode.TRUSTED_LAN if self.TRUSTED_LAN_MODE else AuthMode.INTERACTIVE

    def is_trusted_lan_auth(self) -> bool:
        return self.auth_mode() == AuthMode.TRUSTED_LAN

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
