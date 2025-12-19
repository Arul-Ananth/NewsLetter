import os
import sys
from enum import Enum
from pathlib import Path
from pydantic_settings import BaseSettings

class AppMode(str, Enum):
    SERVER = "SERVER"
    DESKTOP = "DESKTOP"

class Settings(BaseSettings):
    # Core
    APP_MODE: AppMode = AppMode.SERVER
    SECRET_KEY: str = "your-secret-key-here"  # TODO: Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI / External Services
    OPENAI_API_BASE: str = "http://localhost:11434"
    OPENAI_MODEL_NAME: str = "mistral:latest"
    SERPER_API_KEY: str = "" # Optional, can be empty for local-only or passed at runtime

    # Data Storage
    DATA_DIR: Path = Path("./data") # Default for Server mode if not set
    
    class Config:
        env_file = ".env"
        extra = "ignore" # Allow extra fields in .env without crashing

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.configure()

    def configure(self):
        """
        Logic to determine where data should be stored based on APP_MODE.
        """
        if self.APP_MODE == AppMode.DESKTOP:
            # Use User's AppData/Home directory for Desktop Mode
            if sys.platform == "win32":
                base_dir = Path(os.environ.get("APPDATA")) / "AeroBrief"
            else:
                base_dir = Path.home() / ".local" / "share" / "AeroBrief"
            self.DATA_DIR = base_dir
        
        # Ensure directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
