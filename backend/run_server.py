import os
import sys
import multiprocessing

# --- 1. SETUP ENVIRONMENT (MUST BE FIRST) ---
# We set these BEFORE importing 'app' so pydantic doesn't crash.
os.environ["APP_MODE"] = "desktop"
os.environ["SECRET_KEY"] = "desktop-local-insecure-key" # Dummy key for local mode
os.environ["DATABASE_URL"] = "sqlite:///./newsroom.db"  # Placeholder, updated later
os.environ["QDRANT_LOCAL_PATH"] = "./qdrant_data"

# Provide dummy values for Cloud keys to satisfy Pydantic validation
# (Since we use Ollama locally, we don't need real keys)
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-desktop"
if "SERPER_API_KEY" not in os.environ:
    os.environ["SERPER_API_KEY"] = "dummy-serper-key"

# --- 2. SETUP PATHS ---
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS # Internal Temp Dir
    exe_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    exe_dir = base_dir

sys.path.insert(0, base_dir)

# --- 3. IMPORT APP (Now safe to import) ---
try:
    from app.main import app
except ImportError as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)

import uvicorn

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Update Paths to be relative to the executable (not temp folder)
    db_path = os.path.join(exe_dir, 'newsroom.db')
    qdrant_path = os.path.join(exe_dir, 'qdrant_data')
    
    # Overwrite with correct absolute paths
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["QDRANT_LOCAL_PATH"] = qdrant_path
    
    print(f">>> Starting Desktop Engine...")
    print(f">>> Database: {db_path}")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        reload=False, 
        workers=1
    )