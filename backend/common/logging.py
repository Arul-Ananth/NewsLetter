import logging
import os


def configure_logging(app_mode: str | None = None, level: str | None = None) -> None:
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    if app_mode:
        os.environ["APP_MODE"] = app_mode

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
