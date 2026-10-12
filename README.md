# ApplyPilot — Local AI-Powered Job Application Assistant

ApplyPilot is a production-quality, local-first job application assistant built for Windows 10/11 PCs, accessible via Google Chrome at `http://127.0.0.1:5173`. It discovers relevant jobs across permitted public feeds, transparently evaluates candidate eligibility, prepares truthful applications without hallucinations, manages local queues, automates supported workflows using visible Playwright sessions, and provides structured manual assistance for restricted platforms (e.g., LinkedIn, Wellfound).

---

## Key Features

1. **Local-First Privacy & Security**:
   - Zero external cloud storage. Candidate profiles, resumes, and telemetry persist exclusively in local SQLite (`data/applypilot.db`).
   - Loopback isolation: Services bind strictly to `127.0.0.1`, rejecting external network connections.
   - Restrictive CORS configured for local dashboard origin only.

2. **Transparent Multi-Factor Fit Scoring**:
   - Normalized weighted criteria:
     - Skills Match (40%)
     - Job Title Relevance (25%)
     - Experience Compatibility (15%)
     - Location & Work-Mode (10%)
     - Employment Type (10%)
   - Dynamically re-normalizes to 100% when you adjust preferences.
   - Identifies mandatory missing criteria and flags jobs as *Ineligible* without fabrication.

3. **Multi-Provider Discovery & Flexible Import**:
   - Authorized/Permitted Public Feeds: RemoteOK and Jobicy API adapters.
   - Manual URL import and single-job entry form.
   - Bulk CSV job import and CSV export.
   - Realistic synthetic demo listings for offline testing.

4. **Multi-Format & Multi-Version Resume Management**:
   - **LaTeX Support (.tex)**: Ingests `.tex` files or pasted LaTeX source, cleans formatting macros, preambles, and environments while preserving structure, headings, and unescaped entities.
   - **PDF Support (.pdf)**: Local text extraction and metadata validation.
   - **Word Support (.docx, .doc)**: Paragraph and table text extraction.
   - **Plain Text & Markdown Support (.txt, .md)**: Ingests plain text files or raw pasted resume text.
   - **Direct Paste / Editor**: Quick creation tab to paste LaTeX code or plain text directly.
   - **Text Inspector**: Modal viewer to inspect extracted plain text from any version to verify parsing quality.
   - **Truthful Candidate Profile**: Never fabricates degrees, credentials, or past employers. Missing data triggers review.

5. **Stateful Application Workflow**:
   - Explicit state machine: `DISCOVERED` -> `MATCHED` -> `QUEUED` -> `PREPARING` -> `AWAITING_REVIEW` -> `READY_TO_SUBMIT` -> `SUBMITTED` / `MANUAL_ACTION_REQUIRED` / `FAILED` / `SKIPPED`.
   - Bounded concurrency of 1: Guaranteed sequential single-thread processing.
   - Configurable session target: 1 to 15 applications per session.
   - Rate-limiting delay preference: 1.0 to 5.0 seconds between attempts.
   - Responsive session controls: Start, Pause, Resume, and Stop Immediately.

6. **Playwright Visible Automation & Safe Simulation**:
   - Visible Chromium window with persistent user data directory (`data/browser_profile`).
   - Diagnostic screenshots on failure (`data/screenshots/`).
   - Safe Simulation Mode enabled by default: Exercises the complete form-filling and verification flow safely offline.
   - Zero CAPTCHA/MFA bypass attempts: Pauses gracefully and preserves session for user intervention.

7. **External Application Queue (Manual Assistance)**:
   - Dedicated workflow for platforms requiring manual submission (e.g. LinkedIn, Wellfound, custom portals).
   - Generates truthful customized cover letters and copies candidate details in one click.
   - User confirmation required before marking external applications as submitted.

8. **Fluent Desktop Design System**:
   - Designed in Windows 11 Fluent dark/light aesthetic.
   - Real persisted metrics calculated from SQLite (no hardcoded sample counts).
   - Comprehensive audit logs with retention policy cleanup.

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: 3.12 or 3.13 (`python --version`)
- **Node.js**: v20 or v24 (`node --version`)
- **Browser**: Google Chrome

---

## Quick Start (Single-Click Launcher)

1. Double-click `start.bat` in the repository root.
2. The launcher will:
   - Check Python and Node.js.
   - Create the Python virtual environment in `backend\venv` if needed.
   - Install backend requirements and Playwright Chromium.
   - Install frontend npm packages if needed.
   - Launch FastAPI backend at `http://127.0.0.1:8000`.
   - Launch Vite frontend at `http://127.0.0.1:5173`.
   - Automatically open Google Chrome to `http://127.0.0.1:5173`.

---

## Manual Installation & Execution

### 1. Backend Setup

```powershell
# Create and activate virtual environment
python -m venv backend\venv
.\backend\venv\Scripts\activate

# Install dependencies
pip install -r backend\requirements.txt

# Install Playwright browser
playwright install chromium

# Start FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Backend OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

```powershell
# In a separate terminal
cd frontend
npm install
npm run dev
```

Dashboard is accessible at `http://127.0.0.1:5173`.

---

## Running Automated Tests

ApplyPilot includes a comprehensive Pytest test suite covering matching algorithms, duplicate prevention, state transitions, session controls, and CSV parsing:

```powershell
.\backend\venv\Scripts\pytest -v
```

All tests execute against an in-memory SQLite database without touching external portals or live job boards.

---

## Project Structure

```
autojobbot/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (health, jobs, queue, profile, settings, history, logs)
│   │   ├── automation/      # Playwright browser manager & simulation runner
│   │   ├── core/            # Configuration, logging, loopback security
│   │   ├── database/        # SQLite session & base model
│   │   ├── models/          # SQLAlchemy models & state machine
│   │   ├── providers/       # RemoteOK, Jobicy, Mock, and CSV providers
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Scoring matcher, duplicate detector, resume parser, task manager
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Unit and integration test suite
│   ├── requirements.txt
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios client & TanStack Query hooks
│   │   ├── components/      # Sidebar, Header, Modals (Import, Breakdown, Review)
│   │   ├── pages/           # 9 functional pages (Dashboard, Jobs, Queue, History, Profile, Preferences, Automation, Logs, Settings)
│   │   ├── types/           # TypeScript interfaces matching backend schemas
│   │   ├── App.tsx          # Router and Fluent theme management
│   │   └── index.css        # Windows 11 Fluent dark/light styling
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/
│   ├── applypilot.db        # SQLite database file
│   ├── browser_profile/     # Persistent user-data directory for Playwright
│   └── screenshots/         # Diagnostic error screenshots
├── resumes/                 # Local candidate resume uploads (PDF / DOCX)
├── logs/                    # Audit logs (applypilot.log)
├── start.bat                # Windows single-click launcher
├── .env.example
├── .gitignore
└── README.md
```

---

## Safety, Privacy & Compliance Guidelines

- **Zero Credential Theft**: ApplyPilot never logs or extracts passwords, cookies, or authorization tokens.
- **No CAPTCHA / MFA Bypass**: Security gates require user interaction. The browser session is preserved visibly for you.
- **Truthful Applications**: Answers to employer questions are pulled strictly from your verified profile. Missing details prompt human review.
- **Platform Boundaries**: Prohibited automated workflows on sites such as LinkedIn are routed to the External Manual Queue with one-click copy helpers.
