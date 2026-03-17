import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to sys.path to allow imports from 'backend'
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.common.config import AppMode, settings
from backend.common.logging import configure_logging


def start_server() -> None:
    logger = logging.getLogger(__name__)
    logger.info("Starting Application as Server...")
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in .env for server mode.")

    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        from backend.common.database import create_db_and_tables
        from backend.server.routers import auth, news

        @asynccontextmanager
        async def lifespan(_: FastAPI):
            create_db_and_tables()
            yield

        app = FastAPI(title="AeroBrief Server", lifespan=lifespan)
        app.include_router(auth.router, prefix="/auth")
        app.include_router(news.router, prefix="/news")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins(),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        uvicorn.run(
            app,
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            reload=False,
            workers=1,
        )

    except ImportError as exc:
        logger.exception("Error starting server: %s", exc)
        logger.error("Ensure 'fastapi', 'uvicorn', 'sqlmodel' are installed.")
        sys.exit(1)


def start_desktop() -> None:
    logger = logging.getLogger(__name__)
    logger.info("Starting Application as Desktop...")
    try:
        from backend.desktop.main import main as desktop_main

        desktop_main()
    except Exception as exc:
        logger.exception("Error starting desktop app: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    settings.configure()
    configure_logging(settings.APP_MODE.value)
    if settings.APP_MODE == AppMode.DESKTOP:
        start_desktop()
    else:
        start_server()
