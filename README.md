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
├── docker-compose.yml
├── render.yaml
├── .gitignore
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

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run migrations to create the SQLite database schema:
   ```bash
   python manage.py migrate
   ```

6. Seed the database with synthetic data:
   ```bash
   python manage.py seed_data
   ```

7. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env if needed (default VITE_API_BASE_URL=/api works with Vite proxy)
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

## Environment Variables

### Backend (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key (generate a strong random string for production) | dev-only-insecure-key-change-me | Yes |
| `DEBUG` | Enable debug mode (True/False) | True | No |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | localhost,127.0.0.1 | Yes |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | http://localhost:5173,http://127.0.0.1:5173 | Yes |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted CSRF origins | http://localhost:5173,http://127.0.0.1:5173 | Yes |
| `SQLITE_DB_PATH` | Path to SQLite database file | db.sqlite3 | No |
| `ML_MODEL_DIR` | Directory containing ML model .pkl files | ml_models | No |
| `PYTHONUNBUFFERED` | Python unbuffered output | 1 | No |
| `MIN_SKILL_MATCH` | Minimum skill match threshold (0.0-1.0) | 0.5 | No |
| `MAX_WORKLOAD_PERCENT` | Maximum workload percentage | 100 | No |
| `HOURS_PER_WORKDAY` | Hours per workday for capacity calculation | 40 | No |

### Frontend (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_BASE_URL` | Base URL for API calls (include /api) | /api | Yes |

## Docker Deployment

### Local Development with Docker Compose

```bash
# Build and start all services
docker compose up --build -d

# Run migrations and seed data
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_data

# Check health
curl http://localhost:8000/api/health/

# Access frontend at http://localhost:5173
# Access backend API at http://localhost:8000/api/
```

### Production Docker Build

**Backend:**
```bash
cd backend
docker build -t workforceai-backend .
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG=false \
  -e ALLOWED_HOSTS=your-backend-domain.com \
  -e CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com \
  -e CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com \
  -e SQLITE_DB_PATH=/app/db.sqlite3 \
  -e ML_MODEL_DIR=/app/ml_models \
  -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
  -v $(pwd)/ml_models:/app/ml_models:ro \
  workforceai-backend
```

**Frontend:**
```bash
cd frontend
docker build -t workforceai-frontend \
  --build-arg VITE_API_BASE_URL=https://your-backend-domain.com/api .
docker run -p 80:80 workforceai-frontend
```

## Render Deployment

### Using render.yaml (Recommended)

1. Push your repository to GitHub/GitLab
2. Connect your repository to Render
3. Render will automatically detect `render.yaml` and create services
4. Configure the following environment variables in Render dashboard:

**Backend Service:**
- `SECRET_KEY` - Auto-generated by Render (or set manually)
- `DEBUG` - `false`
- `ALLOWED_HOSTS` - Your backend domain (e.g., `workforceai-backend.onrender.com`)
- `CORS_ALLOWED_ORIGINS` - Your frontend domain (e.g., `https://workforceai-frontend.onrender.com`)
- `CSRF_TRUSTED_ORIGINS` - Your frontend domain
- `SQLITE_DB_PATH` - `/app/db.sqlite3`
- `ML_MODEL_DIR` - `/app/ml_models`
- `PYTHONUNBUFFERED` - `1`

**Frontend Service:**
- `VITE_API_BASE_URL` - Your backend API URL (e.g., `https://workforceai-backend.onrender.com/api`)

5. Add a persistent disk to the backend service:
   - Name: `backend-data`
   - Mount Path: `/app`
   - Size: 1 GB (or more)

### Manual Render Setup

If not using `render.yaml`:

**Backend Service:**
- Runtime: Docker
- Dockerfile: `./backend/Dockerfile`
- Build Command: (empty - handled by Dockerfile)
- Start Command: (empty - handled by Dockerfile)
- Health Check Path: `/api/health/`
- Environment Variables: See above
- Persistent Disk: Mount at `/app`

**Frontend Service:**
- Runtime: Docker
- Dockerfile: `./frontend/Dockerfile`
- Build Command: (empty)
- Start Command: (empty)
- Environment Variables: `VITE_API_BASE_URL=https://your-backend-domain.com/api`

## Database Persistence Warning

**IMPORTANT:** The current project uses SQLite for simplicity.

- Render's default filesystem is ephemeral - database changes will be lost on redeploy unless you configure a **persistent disk**.
- The `render.yaml` includes a disk configuration for the backend service.
- For production scale, multi-instance deployments, or concurrent writes, **PostgreSQL is strongly recommended**.
- To migrate to PostgreSQL: Update `DATABASES` in `config/settings.py` to use `dj_database_url` with a PostgreSQL connection string (already supported via `DATABASE_URL` env var).

## ML Model Deployment

The three pre-trained models must be present in the `ML_MODEL_DIR`:
- `task_success_model.pkl`
- `sla_model.pkl`
- `completion_time_model.pkl`

These are tracked in git and included in the Docker image. In production, ensure the persistent disk or Docker volume includes the `ml_models/` directory.

## Health Check

The backend exposes a health endpoint at `GET /api/health/`:

```json
{
  "status": "ok",
  "database": "ok",
  "ml_models": "ok",
  "ortools": "ok"
}
```

Returns `200 OK` if all systems operational, `503 Service Unavailable` otherwise.

## Local Development Commands

```bash
# Backend
cd backend
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py seed_data
python manage.py collectstatic --noinput
python manage.py runserver

# Frontend
cd frontend
npm install
npm run build
npm run dev

# Docker
docker compose build
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_data
docker compose exec backend python manage.py system_check_ai

# Health check
curl http://localhost:8000/api/health/
```

## Testing

```bash
# Backend tests
cd backend
python manage.py test

# ML model validation
python manage.py test_ml_models
python manage.py test_employee_ranking
python manage.py test_allocation
python manage.py test_reallocation

# System check
python manage.py system_check_ai
```

## Troubleshooting

### ML Models Not Loading
- Verify `ML_MODEL_DIR` points to the correct directory
- Check that all three `.pkl` files exist in that directory
- Ensure Python version matches model training version (3.13)

### CORS Errors
- Verify `CORS_ALLOWED_ORIGINS` includes your frontend origin
- Check `CSRF_TRUSTED_ORIGINS` matches for POST requests
- Ensure no trailing slashes in origin URLs

### Database Issues
- Run `python manage.py migrate` to apply migrations
- Check `SQLITE_DB_PATH` is writable
- For Render: verify persistent disk is mounted at `/app`

### Static Files Not Served
- Run `python manage.py collectstatic --noinput`
- Verify `STATIC_ROOT` is configured and accessible

### OR-Tools Not Available
- Ensure `ortools` is in requirements.txt
- In Docker: the base image includes system dependencies

## How ML Works

The system loads three pre-trained `.pkl` models (`task_success_model.pkl`, `sla_model.pkl`, `completion_time_model.pkl`). When a new task is analyzed, `feature_service.py` computes all necessary features (e.g. `skill_match_score`, `workload_capacity`, `availability_score`). The models are then run on these features for all eligible candidates. A combined `suitability_score` is calculated based on success probability (50%), SLA probability (30%), and time score (20%).

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