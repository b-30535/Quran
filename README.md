# Noor Al-Quran Ultimate

Development-only project. Do not deploy to production or change the live app until the owner explicitly approves the final release.

## Current development milestone

- `pwa/`: responsive installable web app shell with Surah reader, Para/Juz browsing, Arabic Uthmani text and Sahih International translation from AlQuran Cloud, audio playback entry point, local favorites/bookmarks/progress, dhikr counter and reminder preference UI.
- `api/index.py`: FastAPI backend foundation for secure registration/login, hashed passwords (scrypt), signed expiring session tokens, user profile, synced favorites/bookmarks/progress, and reminder preferences.
- `requirements.txt`: Python backend dependencies.
- `vercel.json`: development routing configuration.

## Configure development backend

1. Create a PostgreSQL database (Neon is a suitable Vercel-compatible choice).
2. Configure development-only environment variables in Vercel:
   - `DATABASE_URL` — PostgreSQL connection string with TLS.
   - `AUTH_SECRET` — long random secret (never commit this value).
   - `ALLOWED_ORIGINS` — exact development preview origin(s).
3. Install Python dependencies from `requirements.txt`.
4. Deploy a **Preview** from the `development` branch only and test registration, login, session expiry, data sync, and error handling.
5. Do not promote to Production until explicit approval.

## Known gaps before release

- Vercel project scope access must be restored before creating a preview deployment or configuring environment variables.
- Quran data is fetched from AlQuran Cloud at runtime; confirm edition attribution, content accuracy, API availability and offline behavior before release.
- Audio playback currently starts the first ayah as a proof of integration, not a complete playlist/player.
- Browser reminder preferences and notification permission are present, but scheduled push delivery is **not implemented yet**. It requires push subscriptions, VAPID credentials, a scheduled job and end-to-end tests. Do not describe reminders as working push notifications until verified.
- Android packaging remains a follow-up after the PWA is approved; use a Trusted Web Activity or Capacitor and test on real devices.
- Add automated backend tests, rate limiting, account recovery, security review, privacy policy and accessibility checks before public launch.

## Content and privacy

Never store plaintext passwords. Never commit production secrets. Use only verified Quran editions and clearly label translations and reciters. Keep user data private and allow users to delete their account and saved data before public release.
