# Deploying OpportunityGenie AI

Two things need to happen: get the **backend** running somewhere public,
then get the **app** in front of people. Below is the fastest realistic
path to "live and clickable today," followed by the slower, real path to
the App Store / Play Store.

This guide assumes no prior deployment experience. Every command is
copy-paste.

---

## Part 1 — Put the backend online (Render)

Render is a good first choice: free-to-cheap, no server management, and
its `render.yaml` support means it can provision the API and the
database together in one step. (Railway or Fly.io work similarly if you
prefer those.)

### 1. Push this code to GitHub

If you haven't already:
```bash
cd opportunitygenie_ai   # wherever you unzipped it
git init
git add .
git commit -m "Initial commit"
```
Then create a new **empty** repository on github.com (don't let it
initialize a README), and follow the "push an existing repository"
instructions it shows you — it'll be three `git remote add` / `git push`
commands.

### 2. Deploy on Render

1. Go to [render.com](https://render.com) and sign up (GitHub login is fastest).
2. Click **New > Blueprint**.
3. Connect your GitHub account and select the repo you just pushed.
4. Render will find `render.yaml` at the root automatically and show you
   a preview: one **Web Service** (`opportunitygenie-api`) and one
   **PostgreSQL database** (`opportunitygenie-db`). Click **Apply**.
5. It'll ask you to fill in the variables marked `sync: false`:
   - `SUPABASE_URL` and `SUPABASE_ANON_KEY` — from your Supabase project
     (Project Settings > API); see `SUPABASE_SETUP.md`
   - `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
   - Leave the three `STRIPE_*` ones blank for now — nothing breaks, the
     billing endpoints just return a friendly "not configured yet" error
     until you're ready to charge people.
6. Deploy. First deploy takes a few minutes. When it's done, Render
   gives you a URL like `https://api.opportunitygenie.org`.

### 3. Confirm it's alive

```bash
curl https://api.opportunitygenie.org/health
```
You should get back `{"status":"ok",...}`. If not, check the **Logs** tab
on the Render service — the most common issue is a typo'd env var.

---

## Part 2 — Create your admin account

There's no seeded admin — by design, per your earlier request. You make
one real person an admin, and only after they've actually signed up.

### 1. Sign up a real account against your live API

Signup now emails a confirmation code (see `SUPABASE_SETUP.md` first).
Easiest is the app itself; via curl it is two calls:
```bash
curl -X POST https://api.opportunitygenie.org/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Your Name", "email": "you@yourdomain.com", "password": "choose-a-real-password"}'

# check your inbox for the 6-digit code, then:
curl -X POST https://api.opportunitygenie.org/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email": "you@yourdomain.com", "code": "123456"}'
```

### 2. Promote that account to admin

The `make_admin` script needs to talk directly to your database. On
Render, open the **opportunitygenie-db** database page and copy the
**External Database URL** (not the internal one — that only works from
inside Render's network).

On your own machine:
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="paste-the-external-database-url-here"
export JWT_SECRET_KEY="anything"   # not used by this script, just needs to be set

python -m app.scripts.make_admin you@yourdomain.com
```
You should see `Admin access granted to you@yourdomain.com.`

### 3. Log in

Log into the app (or hit `/auth/login`, then `/auth/me`) with that
account — `is_admin` will now be `true`, and the Admin console becomes
reachable from the Profile tab.

---

## Part 3 — Get the app in front of people, fast (web build)

Native app store review takes days to weeks. If you want something
live *today* to test with real users, build the Flutter app for web and
drop it on Netlify — no app store, no waiting.

```bash
cd mobile
flutter build web --dart-define=API_BASE_URL=https://api.opportunitygenie.org
```

Go to [app.netlify.com/drop](https://app.netlify.com/drop) and drag in
the `mobile/build/web` folder. Netlify gives you a live URL in seconds
(e.g. `https://opportunitygenie-ai.netlify.app`).

**Then go back to Render** and update `ALLOWED_ORIGINS` on the API
service to your real Netlify URL instead of `*` (Settings > Environment
> edit the variable, then it auto-redeploys). Leaving it as `*` works
for testing but is sloppier than you want once real users are on it.

> Note: `flutter_secure_storage` on web falls back to browser storage
> rather than true OS-level secure storage. Fine for testing, worth
> revisiting before you rely on it for real user sessions at scale.

---

## Part 4 — The real App Store / Play Store path

This part genuinely needs you (or someone with these accounts) — no way
around the identity verification and legal agreements involved.

**iOS:**
1. Apple Developer Program — $99/year, developer.apple.com/programs.
2. `flutter build ipa --dart-define=API_BASE_URL=https://api.opportunitygenie.org`
3. Upload via Xcode or the Transporter app.
4. Set up the listing in App Store Connect (screenshots, description,
   privacy policy URL — you'll need one; even a simple hosted page
   describing what data you collect is required).
5. TestFlight first for beta testing, then submit for review.

**Android:**
1. Google Play Console — $25 one-time, play.google.com/console.
2. `flutter build appbundle --dart-define=API_BASE_URL=https://api.opportunitygenie.org`
3. Upload the `.aab` file to Play Console.
4. Complete the store listing (same requirements: screenshots,
   description, privacy policy).
5. Submit for review — usually faster than Apple's.

Both stores will ask about data collection (you're collecting emails,
academic data) — answer that honestly in their data-safety
questionnaires; it's a standard, expected step, not a blocker.

---

## When something breaks

- **Backend 500s on Render**: check the Logs tab first. Most common:
  missing env var, or `DATABASE_URL` not yet propagated right after
  first deploy (wait ~30s and retry).
- **App can't reach the API**: double check the `API_BASE_URL` you built
  with actually matches your Render URL, and that `ALLOWED_ORIGINS`
  on the backend includes wherever the app/web build is served from.
- **AI Advisor returns "not configured"**: `ANTHROPIC_API_KEY` isn't set
  on Render — go set it under Environment and it'll redeploy.
