# Lumeward

Lumeward is a hybrid AI brief/newsletter application with shared backend services and two runtime modes:

- `SERVER` for web clients
- `DESKTOP` for the PySide6 desktop app

## Current Implemented State

### Core runtime

- CLI startup overrides are implemented in `backend/main.py`:
  - `--mode {desktop,server}`
  - `--auth-mode {trusted_lan,interactive}`
  - `--host`
  - `--port`
  - `--reload`
- Runtime precedence is:
  - CLI flags
  - environment variables
  - code defaults

### Auth and deployment

- Web/server mode supports:
  - `AUTH_MODE=trusted_lan`
  - `AUTH_MODE=interactive`
- Desktop mode always resolves to the local trusted-lan style path.
- `modes.md` is the operator-facing source of truth for runtime and trust modes.

### Remote engine support

- Lumeward can call an OpenAI-compatible engine running on another machine.
- When enabled, Lumeward keeps auth, memory, telemetry, persistence, and tool policy locally and sends only model requests to the remote engine.

### Desktop telemetry and clipboard

- Desktop telemetry is opt-in.
- Clipboard collection is opt-in.
- Raw clipboard text is separately opt-in.
- Recent clipboard-history queries use a direct recent-clipboard path instead of only semantic memory retrieval.

### Search behavior

- Serper is used when a Serper key is available.
- Desktop fallback search uses `ddgs` + extraction when Serper is unavailable.
- Search mode is surfaced in the desktop UI.

### Desktop UI

- The desktop UI is now framed as a brief assistant rather than only a newsletter form.
- The main desktop screen is organized into:
  - `Ask`
  - `Guide`
  - `Run`
  - `Result`
- Desktop settings include theme preference:
  - `System Default`
  - `Dark`
  - `Light`
- Theme changes apply immediately without restart.
- The main desktop view is wrapped in a scroll area so the whole screen can be reached with the mouse wheel.

### Desktop bridge

- The local browser bridge stays on loopback.
- It uses a runtime-generated bridge token header.
- Uvicorn lifespan handling is disabled for the bridge app to avoid noisy shutdown `CancelledError` traces.

## Project Layout

- `backend/` shared backend, server mode, desktop mode
- `frontend/` React + Vite web client
- `docs/` architecture, audits, prompts, roadmap/status notes
- `scripts/verify/` verification scripts
- `scripts/manual/` manual checks
- `scripts/dev/` build and operational scripts
- `packaging/pyinstaller/` desktop packaging specs

## Startup

Server:

```powershell
cd C:\Dev\lumeward
.\venv_win\Scripts\python.exe backend\main.py --mode server
```

Desktop:

```powershell
cd C:\Dev\lumeward
.\venv_win\Scripts\python.exe backend\main.py --mode desktop
```

Interactive server:

```powershell
.\venv_win\Scripts\python.exe backend\main.py --mode server --auth-mode interactive --host 0.0.0.0 --port 8000
```

## Docs

- [modes.md](./modes.md): runtime modes, trust profiles, connectivity profiles
- [docs/architecture/overview.md](./docs/architecture/overview.md): current codebase structure and implementation shape
- [docs/security.md](./docs/security.md): trust boundaries and safeguards
- [docs/roadmap.md](./docs/roadmap.md): implemented work so far plus possible future items that may or may not happen

## Future Items

Potential future work is tracked in [docs/roadmap.md](./docs/roadmap.md).
Those items are directional only unless explicitly scheduled; they are not commitments.



## Linux Desktop Setup

For Linux or WSL desktop testing, use the Linux-specific desktop requirements file:

```bash
cd /mnt/c/Dev/lumeward
python3 -m venv .venv_linux
source .venv_linux/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-desktop-linux.txt
python backend/main.py --mode desktop
```

Recommended OS packages on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-venv libgl1 libglib2.0-0 libxkbcommon-x11-0 libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 gnome-keyring libsecret-1-0 libsecret-1-dev dbus-user-session
```

Notes:
- `requirements-desktop-linux.txt` adds the CrewAI Google provider extra used by `LLM_PROVIDER=google`.
- It also installs Linux keyring backends so desktop secret access works more reliably for other developers.
- In WSL, a working GUI environment is still required for PySide6 desktop mode.
