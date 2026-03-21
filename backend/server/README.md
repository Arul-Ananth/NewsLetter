# Server Runtime

- `backend/server/app.py` owns FastAPI creation, router registration, middleware, and lifespan.
- `backend/main.py` only selects mode and launches the server runtime.
- Routes should depend on the auth resolver and typed schemas, not direct mode flags.
