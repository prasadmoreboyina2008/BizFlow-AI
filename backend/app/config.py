import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_SECRET = os.getenv("APP_SECRET") or secrets.token_urlsafe(32)
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[1] / "bizflow.db"))
