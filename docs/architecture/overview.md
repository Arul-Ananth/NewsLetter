# Architecture Overview

## Runtime Modes

- `SERVER` mode runs FastAPI for web clients.
- `DESKTOP` mode runs PySide6 + qasync with local bridge + telemetry runtime.

## Backend Structure

- `backend/common/`
  - `config.py` shared settings and env loading
  - `database.py` SQLModel engine/session/migrations
  - `models/` API and DB models
  - `services/`
    - `auth/` authentication utilities (JWT/password hashing)
    - `llm/` provider factory, tool policy, crew builders, newsletter orchestration
    - `memory/` memory sanitizer + vector DB helpers
    - `search/` web search tools and fallbacks
    - `telemetry/` event bus, ingestion, workers, consent
- `backend/server/`
  - FastAPI routers and auth dependencies
- `backend/desktop/`
  - Qt desktop UI, workers, bridge process, preferences/security

## Service Layer Conventions

- Keep orchestration modules thin and composable.
- Keep provider-specific logic isolated under `services/llm/`.
- Keep storage/memory code isolated under `services/memory/`.
- Keep external network tools isolated under `services/search/`.
- Use compatibility wrappers in `services/*.py` only for transition/import stability.

## Frontend Structure

- `frontend/src/pages/` route pages
- `frontend/src/components/` reusable UI components
- `frontend/src/services/` API client and request helpers
- `frontend/src/context/` app settings/state context
- `frontend/src/theme/` theme and providers

## Scripts

- `scripts/verify/` automated verification checks only
- `scripts/manual/` manual diagnostics
- `scripts/dev/` operational/developer scripts (build/firewall helpers)
- `scripts/fixtures/` sample data/fixtures for tests and ingestion flows
