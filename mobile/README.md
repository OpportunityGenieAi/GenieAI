# OpportunityGenie AI — Mobile (Flutter)

Talks to the FastAPI backend in `../backend`. No mock data, no local
fake auth — every screen calls the real API.

## Setup

```bash
flutter pub get
```

Point it at your backend with `--dart-define` (see `lib/config/env.dart`
for the default):

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator → host machine
flutter run --dart-define=API_BASE_URL=http://localhost:8000  # iOS simulator / web
flutter build apk --dart-define=API_BASE_URL=https://api.yourdomain.com   # release build
```

## Before you trust this as launch-ready

This was written without access to the Flutter SDK, so it has **not**
been run through `flutter analyze` or compiled. Run both and fix
whatever surfaces — normal for a first pass, but don't skip it.

```bash
flutter analyze
flutter test   # no tests are included yet — add some before shipping
```

## Structure

```
lib/
  main.dart, app.dart          — entrypoint, MaterialApp, providers
  config/env.dart              — API base URL (dart-define overridable)
  theme/app_theme.dart         — colors + Inter font, matching the reference design
  models/                      — plain Dart classes mirroring the backend's schemas
  services/                    — HTTP calls (api_client.dart is the shared client)
  providers/                   — ChangeNotifier state (Provider package)
  screens/
    auth/                      — login, signup, forgot password
    home/, match/, tracker/, advisor/, profile/  — the five bottom tabs
    admin/                     — real-admin-only scholarship CRUD
  widgets/                     — scholarship_card, feature_gate (locked-tab prompt)
  l10n/app_strings.dart        — simple map-based i18n (en/es/fr) — no codegen needed
```

## Font note

The reference design's font is closest to Apple's SF Pro, which can't
legally be bundled outside Apple's own platforms. This app uses **Inter**
via `google_fonts` — the standard open-source substitute, visually very
close. `google_fonts` fetches font files at runtime by default; for a
fully offline-capable app, switch to bundling Inter as a local asset
font instead (see the google_fonts package docs for `GoogleFonts.config`).

## Icons

Bottom tab icons use Flutter's built-in Material icon set
(`Icons.home_outlined`, `Icons.bolt_outlined`, etc.) rather than custom
SVGs, to keep the app buildable without extra asset pipeline setup.
Swap in a custom icon font or SVG set later if you want an exact visual
match to a specific icon style.
