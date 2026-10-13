# Noor Al-Quran Ultimate — Backend

Private development foundation. This folder is **not deployed** by this commit.

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- MongoDB Atlas with PyMongo's asynchronous client
- Pydantic Settings for environment configuration

## Run locally
From the repository root:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and set MONGODB_URI if you want database connectivity.
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs during development.

## Initial endpoints
- `GET /` — API identity
- `GET /api/v1/health` — liveness check
- `GET /api/v1/ready` — whether MongoDB is connected

The service can start without a database to support frontend development, but database-backed features are unavailable until `MONGODB_URI` is configured. Do not commit `.env`, database credentials, JWT secrets, or API keys.

## Security and religious-content rules
- CORS origins must be explicitly configured for the eventual deployed frontend.
- Keep credentials in hosting environment variables, never in frontend code or Git.
- Add authentication, rate limiting, request validation, audit-safe logging, and tests before exposing user accounts publicly.
- Use trusted Quran text and translation datasets/APIs; do not generate or alter Quran text with an LLM.
- Clearly label AI-generated explanations and cite trusted references. The assistant must not present itself as a mufti or issue definitive fatwas.

## Planned modules
1. Authentication and user profiles
2. Prayer logs and reports
3. User settings and location preferences
4. Bookmarks and reading progress
5. Zikr / Azkar records
6. Backup and account data export

No public deployment should happen until the user explicitly approves the release.
