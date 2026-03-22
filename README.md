Lumeward Desktop Notes

- OCR requires `easyocr` and `Pillow`.
- The browser bridge tries port `12345` first, then falls back to an OS-assigned port and logs the selected port in the output pane.
- The web app now supports two explicit auth modes:
  - `AUTH_MODE=trusted_lan`: shared LAN user, no browser sign-in required
  - `AUTH_MODE=interactive`: sign-in/sign-up screens stay active and routes require an authenticated principal

Project Layout

- `backend/` application backend (shared + server + desktop)
  - `backend/common/services/auth/` auth providers, session transport, resolver, and identity store helpers
  - `backend/common/services/llm/` LLM provider + crew orchestration
  - `backend/common/services/memory/` memory sanitizer + vector helpers
  - `backend/common/services/search/` web search tools
  - `backend/common/services/telemetry/` telemetry pipeline
- `frontend/` React + Vite web client
  - `frontend/src/features/auth/` non-trusted-LAN auth UI and client state
- `scripts/verify/` verification scripts
- `scripts/manual/` manual checks
- `scripts/dev/` operational/dev scripts (build and firewall helpers)
- `scripts/fixtures/ingestion/` sample ingestion fixtures
- `docs/architecture/` architecture and remediation docs
- `docs/audits/` issue audits and findings
- `docs/prompts/` system/context prompts
- `packaging/pyinstaller/` desktop packaging specs

Server configuration

- Backend networking uses env vars:
  - `SERVER_HOST` (default `127.0.0.1`)
  - `SERVER_PORT` (default `8000`)
  - `CORS_ALLOWED_ORIGINS` (comma-separated, default `http://localhost:5173`)
- Auth is mode-driven:
  - `AUTH_MODE=trusted_lan` for private LAN access
  - `AUTH_MODE=interactive` for sign-in/sign-up + authenticated API access
  - `TRUSTED_LAN_MODE` remains a backward-compatible fallback for older env files
- Frontend API base URL uses `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`).
- Runtime overrides are also available from the CLI:
  - `python backend/main.py --mode desktop`
  - `python backend/main.py --mode server --host 0.0.0.0 --port 8000`
  - `python backend/main.py --mode server --auth-mode interactive --reload`

Remote engine configuration

- Lumeward can call an OpenAI-compatible engine running on another machine.
- Set:
  - `ENGINE_ENABLED=true`
  - `ENGINE_BASE_URL=http://<engine-host>:<port>/v1`
  - `ENGINE_API_KEY=<service-key>`
  - `ENGINE_MODEL_NAME=<remote-model>` or reuse `OPENAI_MODEL_NAME`
- When enabled, the backend keeps auth, memory, telemetry, search policy, and persistence locally and sends only model requests to the remote engine.
- The engine URL must match the configured allowlist exactly; the backend will reject other private-network outbound targets.

Example trusted-LAN setup

Backend machine `.env`:

```env
APP_MODE=SERVER
SECRET_KEY=replace_me
AUTH_MODE=trusted_lan
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
CORS_ALLOWED_ORIGINS=http://192.168.1.20:5173
TRUSTED_LAN_USER_EMAIL=local@lan
TRUSTED_LAN_USER_NAME=Trusted LAN User
```

Frontend machine env (for Vite):

```env
VITE_API_BASE_URL=http://192.168.1.10:8000
```

Example interactive setup

```env
APP_MODE=SERVER
SECRET_KEY=replace_me
AUTH_MODE=interactive
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
CORS_ALLOWED_ORIGINS=http://192.168.1.20:5173
```

Networking note

- Open inbound firewall access to `SERVER_PORT` on the backend machine for LAN clients.
- `trusted_lan` is for private LAN use only.
- `interactive` now uses server-stored opaque sessions exposed through a transport-neutral auth resolver so future cookie, token, or external-provider adapters can be added without rewriting business routes.
- The remote engine should stay private to the backend; do not expose it directly to browsers.
