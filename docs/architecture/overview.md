# Architecture Overview

## Runtime Modes

- `SERVER` mode runs FastAPI for web clients.
- `DESKTOP` mode runs PySide6 + qasync with a local bridge and background telemetry runtime.
- Runtime resolution is centralized in `backend/main.py` and follows:
  - CLI flags
  - environment variables
  - code defaults

## Current Implemented Architecture

### Backend core

- `backend/common/config.py`
  - shared settings, mode/auth resolution, desktop data-dir selection
- `backend/common/database.py`
  - SQLModel engine/session setup
- `backend/common/services/`
  - `auth/` web identity/session helpers
  - `llm/` provider factory, tool policy, crew builders, newsletter/brief orchestration
  - `memory/` vector and clipboard-history retrieval helpers
  - `search/` Serper and desktop fallback search
  - `telemetry/` consent, ingestion, workers, session/profile rollups

### Server mode

- App factory lives in `backend/server/app.py`.
- Web auth supports `trusted_lan` and `interactive` modes.
- Remote OpenAI-compatible engine support is optional and stays behind the backend.

### Desktop mode

- Desktop entrypoint lives in `backend/desktop/main.py`.
- Desktop startup now applies saved theme preference before showing the main window.
- The main desktop UI is organized into:
  - `Ask`
  - `Guide`
  - `Run`
  - `Result`
- The desktop UI is scrollable at the page level and still keeps output telemetry on the result pane.
- Desktop settings now group:
  - appearance
  - API keys
  - ingestion
  - privacy

### Search and current-date behavior

- Search mode resolves to `serper`, `fallback`, or `disabled`.
- Desktop fallback search uses `ddgs` plus extraction.
- Time-sensitive prompts are grounded to runtime date context.
- Clipboard-history prompts use a direct recent-clipboard path before falling back to semantic memory.

### Desktop bridge

- The bridge is loopback-only and token-protected.
- It prefers port `12345`, then falls back to an OS-assigned port.
- Uvicorn lifespan is disabled for the bridge app to prevent shutdown noise.

## Service Layer Conventions

- Keep orchestration modules thin and composable.
- Keep provider-specific logic isolated under `services/llm/`.
- Keep storage/memory code isolated under `services/memory/`.
- Keep external network tools isolated under `services/search/`.
- Use compatibility wrappers in `services/*.py` only for transition/import stability.

## Scripts and Docs

- `scripts/verify/` automated verification checks only
- `scripts/manual/` manual diagnostics
- `scripts/dev/` operational/developer scripts
- `docs/security.md` trust boundaries and safeguards
- `modes.md` runtime/trust profile documentation
- `docs/roadmap.md` implemented work and optional future directions

## Possible Future Directions

These are not commitments unless explicitly scheduled:

- stronger public-internet deployment hardening
- per-user memory isolation across all web modes
- richer desktop visual polish beyond the current structure/theme work
- a dedicated remote job/code-execution engine separated from the LLM provider path
- deeper response typing and billing/accounting cleanup
- further pruning of legacy compatibility wrappers after import migration finishes
