import sqlite3
import os
from pathlib import Path

class RelationalDB:
    def __init__(self):
        app_data = os.environ.get('APPDATA')
        if not app_data:
            # Fallback for Linux/WSL if needed
            app_data = os.path.expanduser("~/.local/share")
        
        self.db_dir = Path(app_data) / "AeroBrief" / "db"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / "aerobrief.sqlite"
        
        self.conn = None
        self.init_db()

    def get_connection(self):
        if not self.conn:
             self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                topic TEXT,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                content TEXT
            )
        ''')
        conn.commit()
