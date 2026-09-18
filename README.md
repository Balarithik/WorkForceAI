# AI Workforce Decision & Resource Allocation Agent

## Project Overview

The AI Workforce Decision & Resource Allocation Agent is an internal workforce/task allocation platform for IT services. It allows managers to enter tasks and uses machine learning models to assess the suitability of all available employees, considering their current workload, experience, skills match, and historical performance. It then uses Google OR-Tools to assign tasks optimally and supports dynamic reallocation when conditions change.

## Architecture

- **Frontend**: React (Vite), Tailwind CSS, React Router, Axios
- **Backend**: Python, Django, Django REST Framework, SQLite
- **Machine Learning**: Scikit-Learn (v1.6.1), Pandas, Numpy, Joblib
- **Optimization**: Google OR-Tools

## Folder Structure

```
WorkForceAI/
├── backend/                  # Django backend
│   ├── config/               # Project settings & URLs
│   ├── workforce/            # Main application app
│   │   ├── services/         # ML and OR-Tools logic
│   │   ├── management/       # Custom commands (e.g. seed_data)
│   ├── ml_models/            # Scikit-learn .pkl models
│   ├── manage.py
│   └── requirements.txt
├── frontend/                 # React frontend
│   ├── src/                  # React source code
│   │   ├── components/       # UI components and layout
│   │   ├── pages/            # View pages (Dashboard, CreateTask, etc)
│   │   └── api.js            # API client
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## Installation & Setup

### Backend Setup

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations to create the SQLite database schema:
   ```bash
   python manage.py migrate
   ```
5. Seed the database with synthetic data:
   ```bash
   python manage.py seed_data
   ```
6. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

### Final QA and deployment

Use Python 3.13 for the serialized ML models. Copy `backend/.env.example` to
`backend/.env` or provide the same variables through the deployment platform.

```bash
cd backend
python manage.py migrate
python manage.py seed_employees
python manage.py system_check_ai
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

`seed_employees` is idempotent and creates or updates the canonical synthetic
profiles `E001` through `E050`. It does not delete existing tasks, assignments,
or employees outside that range. The application reads employees, tasks,
assignments, events, dashboard metrics, and predictions from the Django API;
React contains no live demo records.

For the frontend, copy `frontend/.env.example` to `frontend/.env` and set
`VITE_API_BASE_URL` to the deployed API URL including `/api`:

```bash
cd frontend
npm ci
npm run build
```

The backend health endpoint is `GET /api/health/`. It reports database status
and whether all three model files loaded. The model files must remain at
`backend/ml_models/`. `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, CORS, and CSRF
trusted origins are configured through environment variables; do not commit a
production secret.

SQLite requires persistent storage in deployment. It is suitable for this
prototype and a single-process demo, but PostgreSQL or another server database
is recommended for production scale and concurrent writes. The Dockerfiles in
`backend/` and `frontend/` provide reproducible image builds; mount persistent
storage for `backend/db.sqlite3` when using SQLite.

Employee workload is persisted in SQLite and calculated centrally as:

```text
workload_percent = baseline_workload_percent
                  + active_assignment_hours / 40 * 100
available_capacity_percent = 100 - workload_percent
```

Completed, cancelled, and reallocated assignments are excluded from active
hours, so recalculation does not double-count or accumulate workload drift.

### Docker ML validation

Docker bypasses the Windows native-DLL policy and executes the existing model
files in a Linux Python 3.13 environment. From the repository root:

```bash
docker compose build
docker compose up -d backend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_employees
docker compose exec backend python manage.py test_ml_models
docker compose exec backend python manage.py test_employee_ranking
docker compose exec backend python manage.py test_allocation
docker compose exec backend python manage.py test_reallocation
```

The validation commands use real employees from SQLite and temporary tasks where
needed; allocation validation cleans up its temporary records. Check the live
status with `GET http://localhost:8000/api/health/`. The compose service mounts
`backend/db.sqlite3` and `backend/ml_models/` so the database and model files
used by validation are the project files.

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

## How ML Works

The system loads three pre-trained `.pkl` models (`task_success_model.pkl`, `sla_model.pkl`, `completion_time_model.pkl`).
When a new task is analyzed, `feature_service.py` computes all necessary features (e.g. `skill_match_score`, `workload_capacity`, `availability_score`).
The models are then run on these features for all eligible candidates.
A combined `suitability_score` is calculated based on success probability (50%), SLA probability (30%), and time score (20%).

## How OR-Tools Works

`allocation_service.py` uses `pywraplp.Solver` to frame task assignment as a linear programming optimization problem. It maximizes the total `suitability_score` while strictly enforcing constraints (e.g. every task must be assigned to exactly one available employee, and no employee exceeds their remaining workload capacity).

## Dynamic Reallocation

If an employee's availability is changed to `UNAVAILABLE` (e.g., from the Employees page), `reallocation_service.py` automatically intercepts this update. It cancels their currently active assignments, recalculates ML features for all other available employees, uses OR-Tools to pick the next best candidate, and creates a `REALLOCATION` event log visible in the Events page.

## Demo Scenario

1. Start both backend and frontend servers.
2. Go to the **Employees** page. Ensure some employees are `AVAILABLE`.
3. Go to **Create Task** and submit a new task requirement.
4. The system will display the AI assignment recommendation. Click **Confirm Assignment**.
5. Note the assigned employee's ID. Go back to the **Employees** page and toggle their status to `UNAVAILABLE`.
6. Go to the **Events** page. You will see real-time logs indicating the employee became unavailable and the task was successfully dynamically reallocated.
