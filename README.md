# WorkForceAI

AI Workforce Decision & Resource Allocation Agent.

WorkForceAI is a local React and Django application that uses employee skills, availability, workload, SLA data, ML predictions, and Google OR-Tools to recommend and create task assignments.

## Features

- Task creation and assignment recommendations
- Skill matching and candidate comparison
- ML predictions for success, SLA probability, and completion time
- Suitability scoring and explanation details
- Workload and availability tracking
- OR-Tools constrained allocation
- Reallocation when an employee becomes unavailable
- SLA risk analysis
- Events, notifications, and decision history
- Task outcome recording and training-data export

## Architecture

- Frontend: React, Vite, React Router, Axios
- Backend: Django and Django REST Framework
- Database: SQLite at `backend/db.sqlite3`
- ML models: `backend/ml_models/`
- Optimization: Google OR-Tools

The frontend uses one environment-driven API base URL:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Requirements

- Python 3.12 or newer
- Node.js and npm
- SQLite, provided through Python

## Backend Setup

From the repository root:

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver 8000
```

### Linux/macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver 8000
```

The backend runs at `http://127.0.0.1:8000`.

## Frontend Setup

Open a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend normally runs at `http://localhost:5173`.

The frontend API base can be changed without source-code edits by setting `VITE_API_BASE_URL` in `frontend/.env`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Local URLs

- Frontend: http://localhost:5173
- Backend: http://127.0.0.1:8000
- API: http://127.0.0.1:8000/api/
- Health: http://127.0.0.1:8000/api/health/

## Environment Variables

Backend variables are documented in `backend/.env.example`:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `SQLITE_DB_PATH`
- `ML_MODEL_DIR`
- `MIN_SKILL_MATCH`
- `MAX_WORKLOAD_PERCENT`
- `HOURS_PER_WORKDAY`

The default SQLite database is resolved to `backend/db.sqlite3`. If `SQLITE_DB_PATH` is relative, it is resolved relative to `backend/`; its parent directory is created automatically. Relative `ML_MODEL_DIR` values are resolved relative to `backend/` as well.

## ML Models

The existing models are loaded from `backend/ml_models/`:

- `task_success_model.pkl`
- `sla_model.pkl`
- `completion_time_model.pkl`

The ML service keeps the existing feature contract and suitability calculation. No fallback or mock model is used when the model files are unavailable.

## Useful Commands

Backend commands, run from `backend/` with the virtual environment active:

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

Frontend commands, run from `frontend/`:

```bash
npm install
npm run build
npm run lint
```

## Project Structure

```text
WorkForceAI/
├── backend/
│   ├── config/
│   ├── ml_models/
│   ├── workforce/
│   │   ├── management/commands/
│   │   ├── migrations/
│   │   └── services/
│   ├── manage.py
│   ├── requirements.txt
│   └── db.sqlite3
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/
│   ├── package.json
│   └── vite.config.js
└── README.md
```
