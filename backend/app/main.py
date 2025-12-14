import os
import sys
import signal

# --- 1. WINDOWS SIGNAL FIX & ENCODING ---
if sys.platform == "win32":
    # Fix Emoji/Unicode crashing the console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding='utf-8')

    unix_signals = ['SIGHUP', 'SIGTSTP', 'SIGCONT', 'SIGQUIT', 'SIGUSR1', 'SIGUSR2']
    for sig_name in unix_signals:
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, signal.SIGTERM)

# --- 2. DESKTOP CONFIGURATION (CRITICAL) ---
# We must set these BEFORE importing 'app.routers' or 'config',
# otherwise they will load the wrong database settings from .env.
os.environ["APP_MODE"] = "desktop"
os.environ["DATABASE_URL"] = "sqlite:///./newsroom.db"
os.environ["QDRANT_LOCAL_PATH"] = "./qdrant_data"

# --- 3. IMPORTS ---
import multiprocessing
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
# Now it is safe to import routers because ENV vars are set
from app.routers import auth, news

# --- 4. PATH SETUP FOR FROZEN EXE ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    sys.path.insert(0, application_path)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Agentic Newsroom API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(news.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print(">>> Starting Local Newsroom Engine...")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        workers=1
    )