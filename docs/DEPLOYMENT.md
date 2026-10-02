# Deployment guide

BizFlow AI deploys as two services: a static React/Vite frontend and a Python/FastAPI API. For a first deployment, use Render for the API and Vercel or Netlify for the frontend.

## Backend (Render)

1. Create a new Web Service connected to this repository.
2. Set the root directory to `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set `APP_SECRET` to a long random value, `FRONTEND_ORIGIN` to the deployed frontend URL, and `DATABASE_PATH` to a persistent disk path such as `/var/data/bizflow.db`.
6. Optionally set `OPENAI_API_KEY` and `AI_MODEL`. The AI key stays in the API service environment and is never sent to the browser.
7. Attach a persistent disk at `/var/data` when using SQLite. For multiple API instances or managed hosting, migrate the data layer to PostgreSQL before scaling horizontally.

## Frontend (Vercel / Netlify)

1. Import the repository and set the project root to `frontend`.
2. Build command: `npm run build`; output directory: `dist`.
3. Add `VITE_API_URL` with the deployed API base URL, for example `https://bizflow-api.onrender.com` (no trailing `/api`).
4. Deploy. Add the final frontend URL to the backend's `FRONTEND_ORIGIN`, then redeploy the API.

## Production notes

- Replace the demo manager credentials with an account store and password hashing before inviting real users.
- Set a unique `APP_SECRET`; the development fallback is not suitable for deployment.
- SQLite is appropriate for the single-instance MVP. Back up its persistent volume and plan a PostgreSQL migration for concurrent deployments.
- Configure HTTPS on both services and restrict CORS to the exact frontend origin.
