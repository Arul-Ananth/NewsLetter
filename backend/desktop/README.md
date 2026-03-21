# Desktop Runtime

- `backend/desktop/main.py` boots Qt, ensures the local desktop identity, and starts the bridge process.
- `backend/desktop/telemetry_manager.py` coordinates collectors and delegates async work to `backend/desktop/services/telemetry_runtime.py`.
- The desktop bridge remains protected by the per-session `X-Bridge-Token` header.
