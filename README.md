# Noor Al-Quran Ultimate

A mobile-first Progressive Web App foundation for Quran tools and prayer tracking.

## First version includes
- Responsive emerald-and-gold dashboard
- Five obligatory prayer status tracking: on-time, late, missed, Qaza, excused
- Optional Sunnah, Nafl, Witr, and Tahajjud status tracking
- Day, week, month, and year summaries
- Local browser storage and JSON export
- Qibla bearing calculation from device location
- PWA manifest and service worker foundation

## Important limitations in this first version
- Prayer records are local to the browser/device. Cloud backup is not connected yet.
- Quran Arabic text, translations, recitation, prayer-time calculations, verified Tafsir, AI, login, and native APK are planned follow-up modules. This UI does not fabricate Quran text.
- Qibla bearing is calculated from location; a live compass heading depends on browser and device sensor support.
- The service worker caches the app shell, not Quran audio or a full offline Quran library.

## Deploy
This is a static site and can be deployed on Vercel by importing this GitHub repository. HTTPS is required for geolocation and normal PWA installation features.

## Next milestones
1. Test and improve PWA installation and offline shell.
2. Add verified Quran content and prayer-time engine.
3. Add backend API, authentication, and MongoDB cloud sync.
4. Add Azkar and Hifz progress modules.
5. Add reference-backed AI assistant.
6. Package a native Android app and test notifications/background behavior.
