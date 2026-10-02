# Deploy BizFlow AI

Deploy the API and frontend as separate services. These instructions use Render for FastAPI and Vercel for the Vite frontend.

## 1. Deploy the API on Render

1. In Render, create a **New > Web Service** and connect the `prasadmoreboyina2008/BizFlow-AI` GitHub repository.
2. Select branch `main` and set **Root Directory** to `backend`.
3. Choose **Python 3**. Set the build command to `pip install -r requirements.txt` and the start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Add these environment variables in the service settings:

   | Key | Value |
   | --- | --- |
   | `APP_SECRET` | A long, private random value |
   | `DEMO_PASSWORD` | A private password for the demo manager and employee logins |
   | `FRONTEND_ORIGIN` | `http://localhost:5173` for the first deploy; replace after deploying the frontend |
   | `DATABASE_PATH` | `/var/data/bizflow.db` |
   | `OPENAI_API_KEY` | Optional; leave unset to use built-in recommendations |
   | `AI_MODEL` | Optional; defaults to `gpt-4o-mini` |

5. Set health check path to `/api/health` if Render offers the option.
6. Attach a persistent disk with mount path `/var/data`, then create the service. The app creates and seeds the SQLite database on startup.
7. When deployment succeeds, open `https://YOUR-API.onrender.com/api/health`. It should return JSON with `"status":"ok"`. The interactive API docs are at `/docs`.

**SQLite persistence:** Render's free web services do not support persistent disks and their local files can be lost on restart, spin-down, or deploy. For a demo where seeded data may reset, a free service can be used. To keep created tasks and employees across restarts, use a paid web service with the `/var/data` disk, or migrate to a managed PostgreSQL database. A Render disk attaches to one service instance, so keep this MVP at one instance.

## 2. Deploy the frontend on Vercel

1. In Vercel, add a project and import the same GitHub repository.
2. Set **Root Directory** to `frontend` and framework to **Vite**.
3. Use `pnpm install` as the install command if Vercel does not detect the lockfile automatically. Set the build command to `pnpm run build` and output directory to `dist`.
4. Add the environment variable `VITE_API_URL` with the API base URL, for example `https://YOUR-API.onrender.com`. Do not add `/api` to the end. Set it for Production (and Preview if you use preview deployments).
5. Deploy. Copy the deployed frontend origin, such as `https://YOUR-PROJECT.vercel.app`.

`VITE_API_URL` is public frontend configuration, not a secret. Never put `OPENAI_API_KEY`, `APP_SECRET`, or `DEMO_PASSWORD` in a `VITE_` variable or in Vercel.

## 3. Connect the frontend and API

1. In Render, change `FRONTEND_ORIGIN` to the exact frontend origin from Vercel (scheme included, no trailing slash), for example `https://YOUR-PROJECT.vercel.app`.
2. Save the setting and redeploy the API.
3. Open the Vercel app and sign in with `manager@bizflow.demo` and the private value you configured as `DEMO_PASSWORD`. Seeded employee addresses use that same demo password.
4. Create a task, assign it, update its status, and check Dashboard, AI Insights, and Reports. The first request to a free Render web service may take about a minute after it has been idle while the instance wakes.

## Updating a deployment

Push changes to GitHub `main`. Render and Vercel can deploy automatically from that branch. After changing `VITE_API_URL`, trigger a new frontend deployment because Vite embeds it during the build. After changing backend environment variables, redeploy the API.

## Before using with real users

The login is a shared-password hackathon demo. Replace it with individual accounts, password hashing, and appropriate access control before production use. Use unique secrets, HTTPS, a persistent database, and restrict CORS to your exact frontend origin.
