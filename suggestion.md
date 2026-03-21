# AeroBrief Dependency Audit, Best-Practice Review, and Readability Suggestions

Date: 2026-03-21

## Scope

This document reviews the third-party modules declared in:

- `requirements.txt`
- `requirements-server.txt`
- `requirements-desktop.txt`
- `frontend/package.json`

The review is based on the current codebase and the latest official documentation available on 2026-03-21. The goal is not to restate each library's manual, but to map:

1. what the project is using,
2. where the current implementation aligns with best practice,
3. where it does not,
4. what to refactor for readability and maintainability.

## Overall Assessment

The project is in better shape than a typical prototype. The recent trusted-LAN, strict-schema, bridge-token, and lazy-initialization changes moved it closer to a defensible baseline.

The main remaining issues are readability and boundary clarity, not just correctness:

- server construction and dependency wiring are still too centralized in `backend/main.py`
- several frontend files still reflect the older auth model and should be pruned or restructured
- response typing is still weaker than request typing
- desktop UI orchestration is concentrated in large files
- compatibility wrappers remain after the service-domain refactor and now reduce clarity

## Dependency Documentation Index

### Python Runtime Dependencies

| Module | Official docs | Current role in repo | Best-practice status | Recommendation |
|---|---|---|---|---|
| `crewai` | https://docs.crewai.com/ | Agent/task orchestration for research and writing flows | Partial | Keep agents/tasks modular. Avoid burying tool policy inside agent setup. Preserve the new `llm/` split and continue moving provider/tool decisions into dedicated builders. |
| `pydantic` | https://docs.pydantic.dev/latest/ | Request/response validation and config models | Good | Recent `ConfigDict(extra="forbid", str_strip_whitespace=True)` change is correct. Next step: replace loose `dict` response fields with typed models. |
| `pydantic-settings` | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ | `.env`-driven settings | Partial | Use `SecretStr` for sensitive config and consider grouping settings by concern (`server`, `desktop`, `telemetry`, `security`) to improve readability. |
| `email-validator` | https://pypi.org/project/email-validator/ | Email validation through Pydantic `EmailStr` | Good | Current usage is appropriate. No direct refactor needed. |
| `litellm` | https://docs.litellm.ai/ | LLM abstraction/provider routing | Partial | Validate provider/model compatibility explicitly at startup instead of allowing late runtime failures. Centralize provider selection and fallback policy in one place. |
| `requests` | https://requests.readthedocs.io/en/latest/ | HTTP client for search/fetch flows | Good | The new retry/session pattern is aligned with docs. Next step: centralize session construction and keep explicit timeouts on every request. |
| `passlib` | https://passlib.readthedocs.io/en/stable/ | Password hashing context management | Partial | Since Argon2 is now in use, keep one hashing policy only. Remove dead token-oriented helpers and simplify the auth API surface. |
| `argon2-cffi` | https://argon2-cffi.readthedocs.io/en/stable/ | Modern password hashing backend | Good | Correct direction. Make sure the hash policy parameters are centralized and not duplicated. |
| `sqlmodel` | https://sqlmodel.tiangolo.com/ | ORM and schema layer for SQLite-backed data | Partial | Session dependency usage is fine. Move schema evolution off ad-hoc startup mutations toward a proper migration tool when schema churn stabilizes. |
| `qdrant-client` | https://python-client.qdrant.tech/ | Vector memory/profile storage | Partial | Lazy embedder initialization was the right move. Next step: isolate vector store lifecycle, collection naming, and payload shape behind one repository layer. |
| `sentence-transformers` | https://www.sbert.net/ | Embedding generation | Partial | Avoid implicit global model state where possible. Make model selection/configuration explicit and cache lifecycle predictable. |
| `fastapi` | https://fastapi.tiangolo.com/ | Server API and desktop bridge API | Partial | Request validation is strong now. Response typing still needs work. Prefer an app factory over building/running the app inline. |
| `uvicorn` | https://www.uvicorn.org/ | ASGI server runtime | Good | Current env-driven host/port handling is correct. Keep operational config in env, not in code. |

### Python Desktop / Local Runtime Dependencies

| Module | Official docs | Current role in repo | Best-practice status | Recommendation |
|---|---|---|---|---|
| `PySide6` | https://doc.qt.io/qtforpython-6/ | Desktop UI | Partial | The UI works, but `main_window.py` is too large. Split widget construction, actions, IPC handling, and generation flow into separate helpers/controllers. |
| `qasync` | https://github.com/CabbageDevelopment/qasync | Async/Qt event-loop integration | Partial | Keep async boundaries narrow. Avoid mixing UI orchestration and background-runtime lifecycle in the same class where possible. |
| `keyring` | https://keyring.readthedocs.io/en/latest/ | Secure local credential storage | Good | Appropriate usage. Keep secrets out of settings serialization and logs. |
| `duckduckgo-search` | https://pypi.org/project/duckduckgo-search/ | Desktop fallback web search discovery | Partial | Re-check maintenance state before expanding use. Keep it behind the search abstraction so it can be swapped cleanly. |
| `trafilatura` | https://trafilatura.readthedocs.io/en/latest/ | Article extraction for fallback search | Partial | Good as a secondary extractor. Add extraction size limits and clearer error metrics if this path becomes more important. |
| `lxml` | https://lxml.de/ | Parser dependency for extraction stack | Good | Keep pinned via the desktop requirement path because the fallback search depends on it operationally. |
| `watchdog` | https://python-watchdog.readthedocs.io/en/stable/ | Folder watch ingestion | Partial | Add clearer debounce/backpressure handling around bursts of file events. |
| `qt-material` | https://pypi.org/project/qt-material/ | Desktop theme styling | Partial | Fine for prototype use. If desktop UI stabilizes, move to a local theme module to reduce theme magic and improve maintainability. |
| `easyocr` | https://www.jaided.ai/easyocr/documentation/ | OCR for snipping flow | Partial | Keep OCR work off the UI thread. Consider configurable language/model loading and lazy initialization if startup time grows. |
| `Pillow` | https://pillow.readthedocs.io/en/stable/ | Image handling in OCR flow | Good | Usage is appropriate. |
| `pypdf` | https://pypdf.readthedocs.io/en/stable/ | PDF text extraction | Good | Keep extraction isolated in ingestion helpers and guard against large-file memory spikes. |
| `python-docx` | https://python-docx.readthedocs.io/en/latest/ | DOCX text extraction | Good | Current role is appropriate. Keep file parsing behind ingestion interfaces. |

### Frontend Runtime Dependencies

| Module | Official docs | Current role in repo | Best-practice status | Recommendation |
|---|---|---|---|---|
| `react` | https://react.dev/ | Frontend UI runtime | Partial | Core usage is fine. Reduce unnecessary provider churn and remove debug logs from render paths. |
| `react-dom` | https://react.dev/ | Browser rendering | Good | No specific issue. |
| `react-router-dom` | https://reactrouter.com/ | Routing | Good | The current simple route setup is fine. Remove dead sign-in/sign-up pages if LAN mode remains primary. |
| `react-markdown` | https://github.com/remarkjs/react-markdown | Newsletter output rendering | Partial | Safe enough for basic Markdown. If richer Markdown is needed later, explicitly define allowed renderers/components instead of expanding implicitly. |
| `@mui/material` | https://mui.com/material-ui/getting-started/ | Main UI component library | Partial | Theme setup is much better after the `extendTheme` fix. Next step: standardize design tokens and move repeated layout primitives into shared components. |
| `@mui/icons-material` | https://mui.com/material-ui/material-icons/ | Icons | Good | No direct issue. |
| `@emotion/react` | https://emotion.sh/docs/introduction | Styling engine | Good | Current usage is conventional. |
| `@emotion/styled` | https://emotion.sh/docs/styled | Styled component wrappers | Good | Current usage is conventional. |
| `@tauri-apps/plugin-shell` | https://v2.tauri.app/plugin/shell/ | Tauri-era capability surface | Needs change | I do not see active usage in the current React app. Remove unless the Tauri path is still a near-term target. |

### Frontend Development Dependencies

| Module | Official docs | Current role in repo | Best-practice status | Recommendation |
|---|---|---|---|---|
| `vite` | https://vite.dev/guide/ | Dev server/build tool | Good | Current usage is standard. |
| `@vitejs/plugin-react` | https://vite.dev/plugins/ | React integration for Vite | Good | Current usage is standard. |
| `typescript` | https://www.typescriptlang.org/docs/ | Type checking | Partial | Types are still too loose in API normalization paths. Remove `any` from `api.ts` first. |
| `@types/node` | https://www.npmjs.com/package/@types/node | Node typings | Good | Standard toolchain dependency. |
| `@types/react` | https://www.npmjs.com/package/@types/react | React typings | Good | Standard toolchain dependency. |
| `@types/react-dom` | https://www.npmjs.com/package/@types/react-dom | React DOM typings | Good | Standard toolchain dependency. |
| `eslint` | https://eslint.org/docs/latest/ | Linting | Good | Keep linting strict enough to catch unused pages/components after the auth pivot. |
| `@eslint/js` | https://eslint.org/docs/latest/use/configure/configuration-files | ESLint flat config support | Good | No issue. |
| `typescript-eslint` | https://typescript-eslint.io/ | TS lint rules/parser | Good | Add rules that discourage `any` and forgotten `console.log` calls. |
| `eslint-plugin-react-hooks` | https://react.dev/reference/eslint-plugin-react-hooks | Hook linting | Good | Keep enabled. |
| `eslint-plugin-react-refresh` | https://github.com/ArnaudBarre/eslint-plugin-react-refresh | Fast refresh safety | Good | No issue. |
| `globals` | https://www.npmjs.com/package/globals | Shared globals list for ESLint | Good | No issue. |
| `babel-plugin-react-compiler` | https://react.dev/learn/react-compiler | Experimental React compiler plugin | Needs change | Use only if you are deliberately adopting React Compiler. Otherwise it increases complexity without current benefit. |
| `@tauri-apps/cli` | https://v2.tauri.app/start/ | Tauri toolchain | Needs change | Remove if the Tauri path is no longer active. Keep only if you plan to revive `legacy_archive/src-tauri`. |

## Project-Specific Best-Practice Findings

### 1. Server Structure

Current strengths:

- host/port/CORS are env-driven
- request models are strict
- trusted-LAN routing no longer depends on browser JWT state

Current issues:

- `backend/main.py` both constructs the FastAPI app and runs Uvicorn
- the app instance is not exposed by a dedicated server factory
- startup concerns, routing, and runtime concerns are mixed together
- `news.py` still returns partially untyped response payloads

Recommended changes:

1. Create `backend/server/app.py` with `create_app() -> FastAPI`.
2. Move lifespan setup into that module.
3. Keep `backend/main.py` as a thin mode switch only.
4. Replace `response_model=dict` and `bill: dict` with explicit Pydantic response models.

### 2. Config and Settings

Current strengths:

- the settings model already centralizes environment-driven behavior
- trusted-LAN settings are explicit

Current issues:

- the settings object is carrying server, desktop, telemetry, search, and security concerns in one flat surface
- sensitive config values should be represented as secrets instead of plain strings where practical

Recommended changes:

1. Introduce grouped settings sections or smaller settings classes.
2. Use `SecretStr` for secrets like API keys and server secrets.
3. Keep derived helpers such as `cors_origins()` close to the relevant config section.

### 3. Auth and Identity Surface

Current strengths:

- trusted-LAN mode is simpler than maintaining a half-finished auth layer
- Argon2 adoption is the correct long-term base

Current issues:

- auth compatibility code remains even though it is non-primary
- some names still imply token-based behavior even though the active path no longer uses it

Recommended changes:

1. Remove dead token-generation helpers once you no longer need compatibility stubs.
2. Rename remaining auth functions so they describe current behavior, not historical behavior.
3. Keep a clean separation between `trusted_lan_identity` and future `interactive_auth`.

### 4. Search and External Tooling

Current strengths:

- `requests.Session` plus retry policy is a strong improvement
- security policy checks at the tool boundary are the right design choice

Current issues:

- HTTP session creation is local to the search module instead of being a reusable network utility
- policy audit is stringly typed and can drift between subsystems

Recommended changes:

1. Move network session creation into a shared HTTP client helper.
2. Formalize audit events with a typed event model or logging helper.
3. Add domain allowlists and timeouts in config instead of code constants.

### 5. Vector Memory and Telemetry

Current strengths:

- lazy embedder initialization reduces startup work
- telemetry has already been pushed off the UI event loop

Current issues:

- telemetry payload, worker coordination, and Qdrant writes still span multiple layers with relatively weak abstractions
- direct `qdrant_client` lifecycle handling is still visible in app-layer code

Recommended changes:

1. Introduce a `MemoryRepository` or `VectorMemoryService` that owns client lifecycle and payload shape.
2. Keep telemetry worker code focused on event processing, not vector-store details.
3. Treat derived-memory records as an internal persistence model, not a cross-layer data shape.

### 6. Desktop UI

Current strengths:

- background workers keep generation and OCR off the main thread
- bridge token protection is now present

Current issues:

- `backend/desktop/ui/main_window.py` is 276 lines and owns too many concerns
- `TelemetryManager` is also acting as a facade, lifecycle manager, and policy bridge
- settings UI is growing and should not keep accumulating unrelated toggles in one class

Recommended changes:

1. Split `MainWindow` into:
   - `MainWindowView` or widget-construction helpers
   - generation controller logic
   - bridge/IPC status handling
   - OCR/snipping coordination
2. Split `SettingsDialog` into sections/widgets:
   - API keys
   - data collection
   - folder ingestion
   - clipboard sensitivity
3. Consider using the Qt worker-object pattern in places where thread classes are currently doing too much directly.

### 7. Frontend Structure

Current strengths:

- the active app flow is much simpler after the trusted-LAN pivot
- route setup is easy to understand

Current issues:

- `SignIn.tsx` and `SignUp.tsx` still exist but are dead in normal routing
- `SettingsContext.tsx` mixes environment detection, persistence, and UI state
- there are debug `console.log` calls in provider render paths
- `api.ts` still normalizes profile data through `any`

Recommended changes:

1. Delete dead auth pages if trusted-LAN mode remains the only planned web mode in the near term.
2. Replace `SettingsContext` state scatter with either:
   - a small reducer, or
   - dedicated persistence hooks like `useLocalStorageSetting`.
3. Remove render-path debug logging.
4. Replace `any` in `api.ts` with typed API payload interfaces.

### 8. Transitional Compatibility Layers

Current strengths:

- compatibility wrappers reduced import breakage during the earlier refactor

Current issues:

- wrappers now reduce readability because the real source of behavior is not obvious

Recommended changes:

1. Finish import migration to domain-specific paths.
2. Delete old compatibility wrapper modules under `backend/common/services/` once all imports are clean.
3. Keep `__init__.py` exports intentional and minimal.

## Readability-First Refactoring Plan

### Priority 1: Clarify entry points and boundaries

1. Introduce `backend/server/app.py` with `create_app()`.
2. Keep `backend/main.py` as mode selection only.
3. Add explicit typed response models for:
   - billing receipt
   - profile response
   - feedback response
4. Move shared HTTP client/session creation into a dedicated helper.

### Priority 2: Remove stale paths after the trusted-LAN pivot

1. Remove dead web auth pages and unused frontend auth helpers.
2. Remove dead token-era backend helpers and wrapper exports.
3. Remove Tauri packages from `frontend/package.json` unless they are still required.
4. Remove `babel-plugin-react-compiler` unless you are actively opting into that toolchain.

### Priority 3: Make desktop code easier to navigate

1. Split `main_window.py` by concern.
2. Split `settings_dialog.py` by section/widget.
3. Introduce a bridge-status helper instead of keeping IPC state logic inside the window class.
4. Extract telemetry startup/shutdown orchestration into a runtime/service helper so `TelemetryManager` becomes smaller.

### Priority 4: Improve type and schema quality

1. Replace all `dict`/`any` response surfaces with typed models/interfaces.
2. Add stricter frontend lint rules for `any`, dead code, and stray console logging.
3. Make profile/memory payload normalization explicit and typed on both backend and frontend.

### Priority 5: Add subsystem docs for future maintainers

1. Add `backend/server/README.md` covering trusted-LAN request flow.
2. Add `backend/desktop/README.md` covering UI thread, worker thread, bridge, and telemetry architecture.
3. Add `backend/common/services/README.md` covering service domains and import rules.

## Highest-Value Concrete Refactors

If I were implementing this next, I would do these in order:

1. Create a proper FastAPI app factory and typed response models.
2. Remove dead frontend auth pages and stale auth-era client code.
3. Replace `Memory.metadata: any` with a typed interface.
4. Split `MainWindow` and `SettingsDialog` into smaller files.
5. Remove transitional wrapper modules after import migration is complete.
6. Prune unused Tauri and experimental React-compiler dependencies if they are no longer part of the product direction.

## Files Worth Refactoring First

- `backend/main.py`
- `backend/server/routers/news.py`
- `backend/common/models/schemas.py`
- `backend/desktop/ui/main_window.py`
- `backend/desktop/ui/settings_dialog.py`
- `backend/desktop/telemetry_manager.py`
- `frontend/src/services/api.ts`
- `frontend/src/context/SettingsContext.tsx`
- `frontend/src/pages/SignIn.tsx`
- `frontend/src/pages/SignUp.tsx`
- `frontend/package.json`

## Conclusion

The codebase is already moving in the right direction. The next gains will come less from adding features and more from removing stale paths, tightening type boundaries, and making runtime boundaries visually obvious in the folder structure and module interfaces.
