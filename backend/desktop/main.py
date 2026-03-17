import asyncio
import logging
import multiprocessing
import sys
import uuid
from pathlib import Path

import qasync
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from sqlmodel import Session, select

# Fix path resolution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.common.config import AppMode, settings
from backend.common.database import create_db_and_tables, engine
from backend.common.logging import configure_logging
from backend.common.models.sql import User, UserWallet
from backend.common.services.auth.auth_utils import get_password_hash
from backend.desktop.services.api_server import run_api_server
from backend.desktop.ui.main_window import MainWindow
from backend.desktop.ui.signal_bus import get_signal_bus

LOCAL_USER_EMAIL = "local@desktop"
LOCAL_USER_NAME = "Desktop User"

logger = logging.getLogger(__name__)


def ensure_local_user() -> int:
    """Ensure a fixed local user exists for Desktop mode (no auth)."""
    with Session(engine) as session:
        statement = select(User).where(User.email == LOCAL_USER_EMAIL)
        user = session.exec(statement).first()

        if not user:
            logger.info("Creating local desktop user.")
            user = User(
                email=LOCAL_USER_EMAIL,
                full_name=LOCAL_USER_NAME,
                hashed_password=get_password_hash("disabled"),
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            wallet = UserWallet(user_id=user.id, balance=999999)
            session.add(wallet)
            session.commit()

        return user.id


def start_api_server(preferred_port: int = 12345):
    ctx = multiprocessing.get_context("spawn")
    ingestion_queue = ctx.Queue()
    status_queue = ctx.Queue()
    stop_event = ctx.Event()
    process = ctx.Process(
        target=run_api_server,
        args=(ingestion_queue, status_queue, stop_event, preferred_port),
        daemon=True,
    )
    process.start()
    return ingestion_queue, status_queue, stop_event, process


def main() -> None:
    settings.APP_MODE = AppMode.DESKTOP
    settings.configure()
    configure_logging(settings.APP_MODE.value)

    app = QApplication(sys.argv)
    app.setOrganizationName("AeroBrief")
    app.setApplicationName("AeroBrief")
    apply_stylesheet(app, theme="dark_teal.xml")

    get_signal_bus()

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    create_db_and_tables()
    user_id = ensure_local_user()

    ingestion_queue = None
    status_queue = None
    api_stop_event = None
    api_process = None
    bridge_warning = None
    try:
        ingestion_queue, status_queue, api_stop_event, api_process = start_api_server()
    except Exception as exc:
        logger.exception("Failed to start local API server: %s", exc)
        bridge_warning = "Browser bridge failed to start; disabled for this session."

    session_id = uuid.uuid4().hex
    window = MainWindow(
        user_id=user_id,
        session_id=session_id,
        ingestion_queue=ingestion_queue,
        status_queue=status_queue,
        api_process=api_process,
        api_stop_event=api_stop_event,
        bridge_warning=bridge_warning,
    )
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
