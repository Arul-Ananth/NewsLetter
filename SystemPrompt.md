# PROJECT CONTEXT: Antigravity (Hybrid AI Newsletter Platform)

**Role:** Lead Full-Stack AI Engineer for "Antigravity."
**Goal:** Build a "Hybrid" AI desktop application that runs locally (Privacy/Free) but can switch to a hosted SaaS backend (Cloud/Power) on demand.
**Target OS:** Windows 11 (Primary).

## 1. ARCHITECTURE: The "Lazy Auth" Hybrid Model
The Frontend (React) acts as the controller, switching API targets based on user preference.
* **Mode A: Local (Default - "Guest"):**
    * **Status:** App launches directly here. No Login required.
    * **Backend:** `http://127.0.0.1:8000` (Local Python Sidecar).
    * **Compute:** Agents run locally on the user's machine.
    * **AI Provider:** User inputs their own API Key (OpenAI/Gemini) OR points to a local Ollama URL.
    * **Context/Memory:** **Opt-In Only.** The AI does *not* read from the local database (Qdrant) unless the user explicitly enables "Use Local Context."
    * **Billing:** Disabled (Free).
* **Mode B: Cloud (Opt-In - "SaaS"):**
    * **Status:** Activated via "Settings" toggle. Triggers Login Screen.
    * **Backend:** `https://api.yournewsletter.com` (Hosted).
    * **Compute:** Agents run on the server.
    * **Auth:** JWT Token required.
    * **Billing:** Active (Checks user credits).

## 2. TECHNOLOGY STACK
* **Frontend:** Tauri v2 + React (Vite/TypeScript). Uses `tauri-plugin-shell`.
* **Backend (Shared Codebase):** Python 3.12 (FastAPI), CrewAI, SQLite/Qdrant.
* **Build System:** PyInstaller for Python backend; `npm run tauri build` for final installer.

## 3. VERSION CONTROL STANDARDS
* **Repository Structure:** Monorepo (Frontend + Backend in one root).
* **Ignored Files (Critical):**
    * **Secrets:** `.env`, `*.pem`, `*.key`.
    * **Build Artifacts:** `src-tauri/target/`, `src-tauri/binaries/`, `backend/build/`, `backend/dist/`.
    * **Dependencies:** `node_modules/`, `venv/`, `venv_win/`, `__pycache__/`.
    * **Local Data:** `newsroom.db`, `qdrant_data/`.

## 4. CURRENT STATUS & BLOCKERS
* **Blocker:** The compiled backend `.exe` is failing to start with `pydantic_core.ValidationError: SECRET_KEY Field required`.
* **UI Status:** Dashboard exists but needs refactoring for "Guest" mode.
* **Git Status:** Repository was re-initialized to fix broken history/structure.

## 5. UI & FEATURE REQUIREMENTS
* **Settings Page:**
    * Toggle: "Enable Cloud Processing" (Triggers Login).
    * Toggle: "Use Local Context" (Opt-in memory retrieval).
    * Input: "OpenAI / Anthropic API Key" (Saved locally).
    * Input: "Serper API Key" (For web search).