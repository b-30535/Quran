# Noor Al-Quran Ultimate — PWA preview

Development-only frontend milestone. Do not deploy to or modify production.

## Included
- Responsive emerald-black and antique-gold interface
- Quran Surah library from AlQuran Cloud API
- Arabic Uthmani text, Sahih International English translation, verse favorites/bookmarks
- Para/Juz browsing, search, audio playback entry point
- Device-local progress and dhikr counter
- Reminder preference UI and notification permission request
- PWA manifest and service worker for app-shell caching

## Preview status
Registration/login is a UI placeholder; it does not create accounts yet. Favorites, bookmarks and progress are stored only in this browser and do not sync between devices. Reminder time is saved locally; dependable scheduled push notifications need a server-side push service and subscription storage. Validate Quran editions and Para boundaries before release. Audio playlist controls and tests remain future work.

## Next milestones
1. Connect secure auth and a managed database through a Vercel-hosted backend (Neon Postgres recommended).
2. Finish translations and contextual metadata for Para reading.
3. Implement push subscriptions and scheduled reminder delivery.
4. Add complete audio playback controls, tests, and accessibility checks.
5. Package the approved PWA for Android using a Trusted Web Activity or Capacitor.

Work only on GitHub development branch until explicit release approval.