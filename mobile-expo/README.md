# OpportunityGenie AI — Mobile (Expo / React Native)

A second mobile client, alongside the Flutter app in `../mobile`. Same
backend, same design, same features — this one exists because Expo's
dev loop (scan a QR code, see changes instantly) is much faster for
day-to-day testing than a Flutter native build cycle. Use whichever
client you'd rather maintain long-term, or keep both if your team has
both skillsets.

## Setup

```bash
npm install
```

Edit `app.json` → `expo.extra.apiBaseUrl` to point at your backend
(defaults to `http://localhost:8000`):

```json
"extra": { "apiBaseUrl": "http://192.168.1.23:8000" }
```

Then:

```bash
npx expo start
```

Scan the QR code with the **Expo Go** app (iOS App Store / Google Play)
on your phone — no Xcode or Android Studio needed for this. Make sure
your phone and computer are on the same Wi-Fi network, and use your
computer's LAN IP (not `localhost`) in `apiBaseUrl` when testing on a
physical device.

- **Android emulator**: use `http://10.0.2.2:8000` instead.
- **iOS simulator**: `http://localhost:8000` works directly.

## Before you trust this as launch-ready

Written without access to a JS/React Native toolchain to actually run
it, so it hasn't been through `npx tsc --noEmit`, ESLint, or an actual
Metro bundle. Brace/paren balance was checked mechanically across every
file, and the API layer mirrors the already-working Flutter client's
calls to the same backend, but budget time for:

```bash
npx expo install --check   # aligns dependency versions with your Expo SDK
npx tsc --noEmit           # type-check
npx expo start             # first real runtime test
```

## Structure

```
App.tsx                        — entrypoint: fonts, providers, navigation
src/
  config/env.ts                — API base URL (from app.json's extra field)
  theme/colors.ts               — palette + Inter font, matching the reference design
  api/                          — fetch-based calls to the FastAPI backend
  context/                      — React Context state (Auth, Profile, Scholarships, Tracker)
  navigation/
    RootNavigator.tsx           — stack: auth screens, GPA converter, admin
    MainTabs.tsx                — the five bottom tabs
  screens/
    auth/, home/, match/, tracker/, advisor/, profile/, admin/
  components/
    ScholarshipCard.tsx, FeatureGate.tsx
```

## Building a real app (not just Expo Go)

Expo Go is for development only. For an installable app or a store
submission, use EAS Build:

```bash
npm install -g eas-cli
eas login
eas build:configure
eas build --platform ios       # or --platform android
```

This produces a real `.ipa`/`.aab` you submit the same way described in
the top-level `DEPLOY.md`.
