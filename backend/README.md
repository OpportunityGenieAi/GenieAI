# OpportunityGenie AI — Backend

FastAPI + PostgreSQL API powering the mobile app: real auth (bcrypt +
JWT), a scholarship database with admin CRUD, the GPA/CGPA converter,
the match engine, the readiness score, the tracker, and a server-side
AI advisor call (your Anthropic key never reaches the client).

There is **no demo or seeded admin account**. The first admin is a real
person you promote yourself — see "Creating your first admin" below.

## 1. Local setup

```bash
cd backend
cp .env.example .env
# edit .env: set JWT_SECRET_KEY (openssl rand -hex 32) and ANTHROPIC_API_KEY at minimum

docker compose up --build
```

This starts Postgres and the API together. The API is now at
`http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.
On first boot it creates all tables and seeds 26 real scholarships.

### Running without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# point DATABASE_URL in .env at a Postgres instance you're running some other way
uvicorn app.main:app --reload
```

## 2. Creating your first admin

1. Sign up a normal account through the app (or `POST /auth/signup`).
2. Promote it:
   ```bash
   python -m app.scripts.make_admin you@yourdomain.com
   ```
3. Log back in (or refresh `/auth/me`) — `is_admin` will now be `true`,
   and the app's Admin console becomes reachable from the Profile tab.

## 3. Required environment variables before you can call it "live"

| Variable | Needed for | Where to get it |
|---|---|---|
| `JWT_SECRET_KEY` | All auth | `openssl rand -hex 32` |
| `DATABASE_URL` | Everything | Your Postgres instance (see hosting below) |
| `ANTHROPIC_API_KEY` | AI Advisor tab | console.anthropic.com |
| `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID_PREMIUM`, `STRIPE_WEBHOOK_SECRET` | Paid subscriptions | Your Stripe Dashboard, once you're ready to charge |
| `ALLOWED_ORIGINS` | CORS | Your app's actual domain(s) |

Nothing charges real money and no AI calls succeed until you fill these in.

## 4. What's real here vs. what still needs your input

**Real and working once deployed:**
- Signup/login with bcrypt password hashing and JWT sessions
- Scholarship database with public browsing + admin-only create/edit/delete
- GPA/CGPA conversion across 13 grading systems
- Match scoring and the readiness score, computed server-side
- Application tracker (save → applied → interview → accepted/rejected)
- AI advisor, calling Anthropic's API from the server (key stays secret)
- Stripe Checkout session creation + webhook to flip a user to "premium"

**Still needs you before a real launch:**
- **Hosting**: this repo doesn't deploy itself. Reasonable options for a
  small team: Render, Railway, or Fly.io for the API + managed Postgres
  add-on (all have free/cheap tiers to start); AWS/GCP if you want more
  control later.
- **Email**: signup confirmation and password reset are handled by
  Supabase Auth (it emails a 6-digit code). Follow `../SUPABASE_SETUP.md`
  to create the project, set custom SMTP, and fill in `SUPABASE_URL` /
  `SUPABASE_ANON_KEY`.
- **Stripe**: create a real Product/Price in your Stripe Dashboard, set
  the three Stripe env vars, and point a webhook endpoint at
  `https://your-domain/billing/webhook`.
- **Domain + HTTPS**: put this behind a real domain with TLS (your
  hosting provider or a reverse proxy like Caddy/Nginx handles this).
- **Database migrations**: this uses `create_all()` on startup, which is
  fine for getting started but doesn't handle schema changes safely once
  you have real user data. Add Alembic before your first production
  schema change.
- **Rate limiting / abuse protection** on `/auth/*` before going public.

## 5. API surface (see `/docs` for full schema)

```
POST   /auth/signup                    (emails a confirmation code)
POST   /auth/verify-email              (code -> logged in)
POST   /auth/resend-code
POST   /auth/login                     (403 = email not verified yet)
POST   /auth/forgot-password/start     (emails a reset code)
POST   /auth/forgot-password/verify    (code + new password)
GET    /auth/me

GET    /scholarships?q=&region=
POST   /scholarships                (admin)
PUT    /scholarships/{id}           (admin)
DELETE /scholarships/{id}           (admin)

GET    /profile/gpa/systems
POST   /profile/gpa/convert
POST   /profile/gpa
GET    /profile/gpa
POST   /profile/academic
GET    /profile/academic
GET    /profile/readiness

GET    /tracker
POST   /tracker/{scholarship_id}
PATCH  /tracker/{scholarship_id}
DELETE /tracker/{scholarship_id}

POST   /advisor/recommend

POST   /billing/create-checkout-session
POST   /billing/webhook
```
