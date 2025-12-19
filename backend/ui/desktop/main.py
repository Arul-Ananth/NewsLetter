import sys
import asyncio
from pathlib import Path
import qasync
from PySide6.QtWidgets import QApplication
from sqlmodel import select, Session

# Fix path resolution
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from backend.server.config import settings, AppMode
from backend.server.database import create_db_and_tables, engine
from backend.server.models.sql import User, UserWallet
from backend.server.services.auth_utils import get_password_hash
from backend.ui.desktop.ui.main_window import MainWindow

def seed_local_admin() -> int:
    """
    Ensures a local admin user exists for Desktop mode.
    Returns the user_id.
    """
    with Session(engine) as session:
        statement = select(User).where(User.email == "admin@local.host")
        user = session.exec(statement).first()
        
        if not user:
            print("Seeding Local Admin User...")
            user = User(
                email="admin@local.host", 
                full_name="Local Admin", 
                hashed_password=get_password_hash("admin")
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Add wallet
            wallet = UserWallet(user_id=user.id, balance=999999)
            session.add(wallet)
            session.commit()
            
        return user.id

def main():
    # 1. Force Desktop Mode
    settings.APP_MODE = AppMode.DESKTOP
    settings.configure()
    
    # 2. Setup Loop
    app = QApplication(sys.argv)
    app.setApplicationName("AeroBrief")
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 3. Init DB & User (Sync for simplicity on startup)
    create_db_and_tables()
    user_id = seed_local_admin()

    # 4. Launch Window
    window = MainWindow(user_id=user_id)
    window.show()

    # 5. Run Loop
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()