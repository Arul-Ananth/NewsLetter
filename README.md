AeroBrief Desktop Notes

- OCR requires `easyocr` and `Pillow`.
- The browser bridge tries port `12345` first, then falls back to an OS-assigned port and logs the selected port in the output pane.

Project Layout

- `backend/` application backend (shared + server + desktop)
  - `backend/common/services/auth/` auth utilities
  - `backend/common/services/llm/` LLM provider + crew orchestration
  - `backend/common/services/memory/` memory sanitizer + vector helpers
  - `backend/common/services/search/` web search tools
  - `backend/common/services/telemetry/` telemetry pipeline
- `frontend/` React + Vite web client
- `scripts/verify/` verification scripts
- `scripts/manual/` manual checks
- `scripts/dev/` operational/dev scripts (build and firewall helpers)
- `scripts/fixtures/ingestion/` sample ingestion fixtures
- `docs/architecture/` architecture and remediation docs
- `docs/audits/` issue audits and findings
- `docs/prompts/` system/context prompts
- `packaging/pyinstaller/` desktop packaging specs

Server/LAN configuration

- Backend networking uses env vars:
  - `SERVER_HOST` (default `127.0.0.1`)
  - `SERVER_PORT` (default `8000`)
  - `CORS_ALLOWED_ORIGINS` (comma-separated, default `http://localhost:5173`)
- Frontend API base URL uses `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`).

Example two-machine LAN setup

Backend machine `.env`:

```env
APP_MODE=SERVER
SECRET_KEY=replace_me
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
CORS_ALLOWED_ORIGINS=http://192.168.1.20:5173
```

Frontend machine env (for Vite):

```env
VITE_API_BASE_URL=http://192.168.1.10:8000
```

Networking note

- Open inbound firewall access to `SERVER_PORT` on the backend machine for LAN clients.
