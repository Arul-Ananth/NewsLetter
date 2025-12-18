import os
import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

# -- DUAL MODE STARTUP --
# Add project root to sys.path to allow imports from 'backend'
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Check for server configuration file
config_file = Path(__file__).parent / ".env" # Check for .env in the same directory as main.py

def start_server():
    print("Starting Application as Server...")
    try:
        import uvicorn
        from fastapi import FastAPI
        from backend.server.routers import auth, news
        from backend.server.database import create_db_and_tables
        
        # Initialize App
        app = FastAPI(title="AeroBrief Server")
        app.include_router(auth.router)
        app.include_router(news.router)
        # Include Routers
        app.include_router(auth.router, prefix="/auth")
        app.include_router(news.router, prefix="/news")
        
        # Create DB
        @app.on_event("startup")
        def on_startup():
            create_db_and_tables()

        origins = [

            "http://localhost:5173",
        ]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
            
        # Run Server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            workers=1
        )
        
    except ImportError as e:
        print(f"Error starting server: {e}")
        print("Ensure 'fastapi', 'uvicorn', 'sqlmodel' are installed.")
        sys.exit(1)

def start_desktop():
    print("Starting Application as Desktop...")
    try:
        # Import local desktop main
        from backend.ui.desktop.main import main as desktop_main
        desktop_main()
    except Exception as e:
        print(f"Error starting desktop app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if config_file.exists():
        start_server()
    else:
        start_desktop()

    
