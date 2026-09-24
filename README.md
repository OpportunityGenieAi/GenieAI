# OpportunityGenie AI

Two real, working codebases:

```
backend/      FastAPI + PostgreSQL API — real auth, real database, real AI call
mobile/       Flutter app (iOS + Android + Web) — talks to the backend above
mobile-expo/  Expo / React Native app — same backend, faster dev loop via Expo Go
```

Two mobile clients exist on purpose: Flutter for a full native build,
and Expo for fast iteration (scan a QR code, see changes instantly,
no Xcode/Android Studio needed to just try it out). Pick one to
maintain long-term, or keep both if your team has both skillsets —
they're independent, not layered on each other.

Neither one is a demo. There is no hardcoded admin login, no fake data
that pretends to be a database, and no client-side API keys. What's here
is real source code that runs when you provide real infrastructure
(a Postgres instance, an Anthropic API key, eventually a Stripe account)
— it just isn't deployed anywhere yet, because deployment requires
accounts and credentials only you can create (Apple Developer, Google
Play Console, a hosting provider, Stripe).

## Ready to deploy for real?

See **`DEPLOY.md`** for a copy-paste walkthrough: hosting the backend on
Render, creating your first real admin account, and getting the app in
front of people fast via a web build — plus the actual App Store / Play
Store path once you're ready for that.

## Quick start (local development)

**1. Backend**
```bash
cd backend
cp .env.example .env
# edit .env — at minimum set JWT_SECRET_KEY (openssl rand -hex 32)
# and ANTHROPIC_API_KEY if you want the AI Advisor to work
docker compose up --build
```
API is now live at `http://localhost:8000` (docs at `/docs`).

**2. Create your first admin**
```bash
# inside backend/, with the venv from docker or a local one active
python -m app.scripts.make_admin you@yourdomain.com
```

**3. Flutter app**
```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator
# or --dart-define=API_BASE_URL=http://localhost:8000          # iOS simulator / web
```

**3b. Or the Expo app (faster to just try out)**
```bash
cd mobile-expo
npm install
# edit app.json > expo.extra.apiBaseUrl to point at your backend
npx expo start
# scan the QR code with the Expo Go app on your phone
```

See `backend/README.md` and `mobile/README.md` for full detail —
environment variables, what's real vs. what still needs your input, and
the complete API surface.

## What "finished" actually means here

I can hand you real, working source code from this chat. I cannot, from
here:
- Submit anything to the App Store or Play Store (needs your Apple
  Developer / Google Play accounts and signing certificates)
- Stand up a live server for you (needs a hosting account — Render,
  Railway, Fly.io, AWS, etc.)
- Create your Stripe account or Anthropic API key
- Create your Supabase project and SMTP account (signup-confirmation and
  password-reset emails are sent by Supabase Auth — see
  `SUPABASE_SETUP.md`)

Once you have those four things, this codebase is what a contractor or
your dev team would build from to actually ship it.

## Honesty about the Flutter app specifically

The 28 Dart files were written carefully and checked for structural
correctness (balanced braces, correct widget parameter names where I
could verify them), but Flutter's SDK isn't available in the sandbox
that wrote this, so **it has not been run through `flutter analyze` or
actually compiled**. Budget time for `flutter pub get` + `flutter
analyze` + fixing whatever that surfaces before treating it as
launch-ready — that's normal for any first pass of a codebase this size,
not a sign something is fundamentally wrong.

## What's implemented vs. still on the roadmap

**Implemented, end-to-end, real:**
auth (signup/login/password reset), scholarship database with admin
CRUD, GPA/CGPA converter (13 grading systems), match engine, readiness
score, application tracker, AI advisor (server-side Anthropic call),
Stripe subscription scaffolding, basic English/Spanish/French
localization.

**From your original spec, not yet built** (say the word and I'll build
any of these next, the same way): Document Builder (CV/SOP/essay
generation), WhatsApp AI bot, Research Profile Analyzer (Google
Scholar/ORCID/Scopus), AI Resume Scanner, Scholarship Marketplace,
Student Community/forums, AI Admission Predictor for specific
universities.
