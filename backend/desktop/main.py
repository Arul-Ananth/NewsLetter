import asyncio
import logging
import sys
from pathlib import Path

import qasync
from PySide6.QtWidgets import QApplication
from sqlmodel import Session, select

# Fix path resolution
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.common.config import AppMode, settings
from backend.common.database import create_db_and_tables, engine
from backend.common.logging import configure_logging
from backend.common.models.sql import User, UserWallet
from backend.common.services.auth_utils import get_password_hash
from backend.desktop.ui.main_window import MainWindow

LOCAL_USER_EMAIL = "local@desktop"
LOCAL_USER_NAME = "Desktop User"


def ensure_local_user() -> int:
    """Ensure a fixed local user exists for Desktop mode (no auth)."""
    logger = logging.getLogger(__name__)
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


def main() -> None:
    settings.APP_MODE = AppMode.DESKTOP
    settings.configure()
    configure_logging(settings.APP_MODE.value)

    app = QApplication(sys.argv)
    app.setApplicationName("AeroBrief")

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    create_db_and_tables()
    user_id = ensure_local_user()

    window = MainWindow(user_id=user_id)
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
