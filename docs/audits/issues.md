# Lumeward Codebase Issue Audit

Date: 2026-03-15
Scope: Static review of backend, desktop, frontend, and verification scripts in this repo, plus build/compile checks.
Checks run:
- `python -m compileall backend` (pass)
- `npm run build` in `frontend/` (fail)

## Critical

1. Cross-user memory rollup can mix and leak user-derived summaries
- Evidence:
  - `backend/common/models/sql.py:48-55` (`DerivedMemory` has no `user_id` column)
  - `backend/common/services/telemetry/workers.py:209-216` (rollup counts all summaries/profiles globally)
  - `backend/common/services/telemetry/workers.py:223-250` (rollup for one `user_id` built from global summaries)
- Impact: User profile memories can include other users' session summaries; privacy and data-isolation violation.

2. "Opt-in" clipboard collection is effectively enabled by default without UI consent controls
- Evidence:
  - `backend/common/config.py:34-35` (`DATA_COLLECTION_ENABLED=True`, `CLIPBOARD_COLLECTION_ENABLED=True`)
  - `backend/desktop/telemetry_manager.py:50-53` (clipboard collector starts automatically when enabled)
  - `backend/desktop/ui/settings_dialog.py:24-47` (no clipboard/data-collection consent toggles)
- Impact: Potential collection of sensitive clipboard text without explicit runtime consent UI.

## High

1. Frontend build is currently broken
- Evidence:
  - Build output: `src/services/api.ts(136,15): error TS6133: 'userId' is declared but its value is never read.`
  - Build output: `src/theme/theme.ts(4,5): error TS2353: 'cssVariables' does not exist in type 'CssVarsThemeOptions'.`
  - `frontend/tsconfig.app.json:21-22` enforces `noUnusedLocals`/`noUnusedParameters`.
- Impact: `npm run build` fails; frontend cannot be shipped from current branch state.

2. Desktop startup depends on missing package `qt_material`
- Evidence:
  - `backend/desktop/main.py:10` imports `qt_material`
  - `requirements-desktop.txt` does not include `qt-material`
- Impact: Desktop app fails at startup in a clean environment.

3. PDF/DOCX ingestion code depends on packages not declared in desktop requirements
- Evidence:
  - `backend/common/services/telemetry/ingestion.py:49` imports `pypdf`
  - `backend/common/services/telemetry/ingestion.py:58` imports `docx`
  - `requirements-desktop.txt` does not include `pypdf` or `python-docx`
- Impact: Ingestion for supported file types (`.pdf`, `.docx`) fails at runtime.

4. Telemetry shutdown can drop queued critical events (including session end)
- Evidence:
  - `backend/desktop/ui/main_window.py:303-305` emits session end, then immediately shuts down telemetry
  - `backend/desktop/telemetry_manager.py:60-66` stops workers and cancels tasks without draining queues
- Impact: Lost telemetry/session events and inconsistent derived memory.

5. Telemetry ingestion and embedding run synchronously on the UI event loop
- Evidence:
  - `backend/desktop/telemetry_manager.py:45-48` starts worker coroutines on main async loop
  - `backend/common/services/telemetry/workers.py:90-140` performs blocking file IO, hashing, embedding, and Qdrant upserts
- Impact: UI stutter/freezes under file ingestion or summary workloads.

6. Server/web networking is hardcoded to localhost
- Evidence:
  - `backend/main.py:48` binds FastAPI to `127.0.0.1`
  - `frontend/src/services/api.ts:3` hardcodes `API_BASE_URL = 'http://127.0.0.1:8000'`
- Impact: Non-local deployments and remote web clients are blocked without code changes.

## Medium

1. Documented CLI mode override is not implemented
- Evidence:
  - `backend/main.py` has no argument parser; startup mode only uses env (`settings.APP_MODE`).
  - Docs mention `python backend/main.py --mode DESKTOP`, but `--mode` is ignored.
- Impact: Operational/docs mismatch; expected startup behavior does not work.

2. Billing uses hardcoded token counts
- Evidence:
  - `backend/server/routers/news.py:41-42` sets `input_tok = 100`, `output_tok = 100`
  - `backend/server/services/billing.py:22` computes cost from those values
- Impact: Incorrect credit deduction and inaccurate usage logs.

3. Desktop settings cannot clear stored API keys
- Evidence:
  - `backend/desktop/ui/settings_dialog.py:52-55` only writes keys when non-empty; no delete path
- Impact: Users cannot remove stale/revoked keys from keyring via UI.

4. `sendFeedback` ignores non-2xx responses
- Evidence:
  - `frontend/src/services/api.ts:135-147` does not check `response.ok`
- Impact: Silent failures in feedback UX; caller cannot reliably detect backend errors.

5. "Web Search (Google)" does not implement distinct Google API behavior
- Evidence:
  - `backend/common/services/search/web_search.py:99-101` only subclasses `WebSearchTool` with renamed metadata
  - No separate Google API request logic exists in class body
- Impact: Tool naming/behavior mismatch; confusing operational behavior and debugging.

6. Server Qdrant local path is relative to current working directory
- Evidence:
  - `backend/common/services/memory/vector_db.py:57` uses `QdrantClient(path="./qdrant_db_local")`
- Impact: Launching from different working directories can create/use different vector stores unexpectedly.

7. `AIWorker` initializes an embedding model that is never used
- Evidence:
  - `backend/desktop/services/ai_worker.py:7, 53-67, 69` initializes `SentenceTransformer`
  - Generated newsletter path uses `newsletter_service` and does not use `self._embedder`
- Impact: Extra startup latency, memory usage, and potential GPU/torch dependency noise.

## Low

1. `requirements-desktop.txt` has duplicates and stale OCR dependency
- Evidence:
  - Duplicate entries: `lxml`, `Pillow`
  - `pytesseract` present while OCR code uses EasyOCR (`backend/desktop/services/ocr_worker.py:46,65`)
- Impact: Larger/less clear dependency footprint; maintenance drift.

2. Verification script dependency gap
- Evidence:
  - `scripts/verify/check_google_models.py:4` imports `python-dotenv`
  - `python-dotenv` is not listed in root requirements files
- Impact: Script may fail in clean env despite core app deps being installed.

