# BizFlow AI

**A calm, clear workspace for getting the right work done.** BizFlow AI is a full-stack business productivity MVP built for AVIRBHAV 2026 Round 2. Managers can coordinate tasks, balance team workload, spot overdue work, and turn activity into a weekly delivery report.

## What works

- Manager sign-in with a demo account and signed bearer token
- Dashboard with task totals, completion, pending, overdue, on-time delivery, productivity, activity charts, and employee workload
- Task creation, assignment, editing, status changes, deletion, search, and filters
- Employee directory with an add employee form and assignment metrics
- AI insights via a backend-only OpenAI API key, with a useful rules-based fallback when no key is configured
- Daily and weekly delivery reports, with text export
- SQLite seed data for Suresh, Krishna, Prasad, Niswanth, and Srinu
- Responsive layouts, form validation, loading and error states, and toast feedback

## Demo login

For local judging, use `manager@bizflow.demo` or a seeded employee address (`suresh@bizflow.demo`, `krishna@bizflow.demo`, `prasad@bizflow.demo`, `niswanth@bizflow.demo`, or `srinu@bizflow.demo`) with the private password you set as `DEMO_PASSWORD` in `backend/.env`. The repository does not contain a default password. This shared-password demo login is for local demonstration only; replace it with proper account management before production use.

## Requirements

- Python 3.10+
- Node.js 18+

## Run locally

Open two terminals from the repository root.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
uvicorn app.main:app --reload --port 8000
```

In Notepad, set `DEMO_PASSWORD` to a private value, save the file, and close Notepad before starting the API.

The API and interactive docs are at `http://localhost:8000` and `http://localhost:8000/docs`. The SQLite database is created and seeded automatically at first startup.

### 2. Frontend

```powershell
cd frontend
corepack pnpm install
corepack pnpm dev
```

Open `http://localhost:5173`. The frontend defaults to the local API. To use another API URL, copy `frontend/.env.example` to `frontend/.env.local`, set `VITE_API_URL`, and restart Vite.

## API overview

All endpoints except `GET /api/health` and `POST /api/auth/login` require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/login` | Sign in |
| GET, POST | `/api/tasks` | List/filter and create tasks |
| GET, PUT, DELETE | `/api/tasks/{id}` | Read, update, and delete a task |
| GET, POST | `/api/employees` | List and add employees |
| GET | `/api/dashboard` | Dashboard statistics and chart series |
| GET | `/api/reports/weekly` | Weekly report data |
| GET | `/api/reports/daily` | Daily report data |
| POST | `/api/ai/analyze` | Task analysis and recommendations |

## Configuration

Copy `backend/.env.example` to `backend/.env`. Set `DEMO_PASSWORD` to a private value before signing in. Set `APP_SECRET` to a long random value for deployments. `OPENAI_API_KEY` is optional; leave it blank to use the built-in rules-based recommendations.

```dotenv
APP_SECRET=your-private-random-secret
DEMO_PASSWORD=your-private-demo-password
OPENAI_API_KEY=
AI_MODEL=gpt-4o-mini
FRONTEND_ORIGIN=http://localhost:5173
DATABASE_PATH=./bizflow.db
```

API keys are only read by the backend. Never put them in a `VITE_` variable or commit `.env` files. The API provides deterministic recommendations without an AI key. If `APP_SECRET` is omitted during local development, the backend creates a temporary random signing secret on startup, so existing sessions expire after a restart.

## Data and design

SQLite access is isolated in `backend/app/database.py`, while API routes, validation schemas, security, configuration, and AI analysis are separate modules. This keeps the storage boundary ready for a PostgreSQL repository implementation. Frontend source lives under `frontend/src` and uses Recharts for live chart data.

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Render API and Vercel/Netlify frontend setup, environment variables, CORS, and persistent database storage.

## License

Hackathon project. Add a license before redistributing.
