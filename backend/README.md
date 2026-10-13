# Noor Al-Quran Ultimate — Backend

Private development foundation. This folder is **not deployed** by these changes.

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- MongoDB Atlas with PyMongo's asynchronous client
- Pydantic Settings
- Argon2 password hashing via pwdlib
- Signed JWT bearer access tokens

## Run locally
From the repository root:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `.env` and configure:
- `MONGODB_URI`: your MongoDB Atlas connection string
- `JWT_SECRET_KEY`: a secret at least 32 characters long; generate locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `CORS_ORIGINS`: exact local or future frontend origins

Start the API from the `backend` directory:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs during development.

## Endpoints
- `GET /` — API identity
- `GET /api/v1/health` — liveness check
- `GET /api/v1/ready` — whether MongoDB is connected
- `POST /api/v1/auth/register` — create an account
- `POST /api/v1/auth/login` — authenticate and receive a short-lived access token
- `GET /api/v1/auth/me` — get the current profile using `Authorization: Bearer <token>`

Registration JSON example:

```json
{
  "display_name": "Demo User",
  "email": "demo@example.com",
  "password": "Use-A-Unique-Password-Here"
}
```

Passwords must be 10–128 characters. Passwords are hashed with Argon2; plaintext passwords are never stored. Access tokens expire after 30 minutes by default. Keep `.env` private and never place secrets in frontend code or Git.

The service can start without a database to support frontend work, but database-backed features require a working `MONGODB_URI`. Do not use the demo HTML for real credentials; its sign-in is simulated locally.

## Security and religious-content rules
- CORS origins must be explicitly configured for the eventual deployed frontend.
- Keep credentials in hosting environment variables, never in frontend code or Git.
- Before public release, add rate limiting, password reset/email verification, account deletion, security review, and broader tests.
- Use trusted Quran text and translation datasets/APIs; do not generate or alter Quran text with an LLM.
- Clearly label AI-generated explanations and cite trusted references. The assistant must not present itself as a mufti or issue definitive fatwas.

## Planned modules
1. Authentication and user profiles (initial API now added)
2. Prayer logs and reports
3. User settings and location preferences
4. Bookmarks and reading progress
5. Zikr / Azkar records
6. Backup and account data export

No public deployment should happen until the user explicitly approves the release.
