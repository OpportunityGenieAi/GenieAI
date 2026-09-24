# Supabase email setup (signup confirmation + forgot password)

How it works: the apps still talk only to your FastAPI backend. The backend
calls Supabase Auth, and Supabase sends the emails (a 6-digit code):

- **Sign up** -> `POST /auth/signup` -> Supabase emails a confirmation code ->
  user types it in the app -> `POST /auth/verify-email` -> logged in.
- **Forgot password** -> `POST /auth/forgot-password/start` -> Supabase emails a
  reset code -> user types code + new password -> `POST /auth/forgot-password/verify`.

Codes are used instead of links so it works identically on iOS, Android,
Expo Go and web, with no deep-link setup.

## 1. Create the Supabase project

1. Sign in at https://supabase.com and create a new project.
2. **Project Settings -> API**: copy the **Project URL** and the **anon** (or
   "publishable") key. You need these two values, nothing else.
   Never use the `service_role` / secret key in this app.

## 2. Turn on email confirmation

**Authentication -> Providers -> Email**: make sure Email is enabled and
**Confirm email** is ON.

**Authentication -> URL Configuration**: set **Site URL** to your web app
(e.g. `https://genie-ai-azure.vercel.app`). Links aren't used, but the default
points to localhost.

## 3. Switch the email templates to codes (important)

**Authentication -> Email Templates** (called "Emails" in newer dashboards).
The default templates contain a link, which the app can't use. Replace the body
of both templates with the code.

**Confirm sign up** - subject `Confirm your OpportunityGenie account`:

```html
<h2>Welcome to OpportunityGenie AI</h2>
<p>Your confirmation code is:</p>
<p style="font-size:28px;font-weight:bold;letter-spacing:6px">{{ .Token }}</p>
<p>Enter it in the app to activate your account. If you didn't sign up, ignore this email.</p>
```

**Reset password** - subject `Reset your OpportunityGenie password`:

```html
<h2>Password reset</h2>
<p>Your reset code is:</p>
<p style="font-size:28px;font-weight:bold;letter-spacing:6px">{{ .Token }}</p>
<p>Enter it in the app with your new password. If you didn't ask for this, ignore this email.</p>
```

## 4. Set up real email delivery (custom SMTP)

Supabase's built-in email sender only delivers to your own team members and is
heavily rate-limited, so real users will NOT get emails without this step.

1. Create a free account at https://resend.com (Brevo, Postmark, SendGrid or
   AWS SES also work) and verify your sending domain (add the DNS records they show).
2. **Authentication -> Emails -> SMTP Settings** (older dashboards: Project
   Settings -> Authentication) -> enable custom SMTP:
   - Host `smtp.resend.com`, Port `465`, Username `resend`
   - Password: your Resend API key
   - Sender email: `no-reply@yourdomain.com`, Sender name: `OpportunityGenie AI`
3. **Authentication -> Rate Limits**: raise "emails sent per hour" if you expect volume.

## 5. Give the backend the two values

Local (`backend/.env`):

```
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

Render: your service -> **Environment** -> add `SUPABASE_URL` and
`SUPABASE_ANON_KEY`, then redeploy.

## 6. Test it

```bash
API=http://localhost:8000     # or your Render URL

curl -X POST $API/auth/signup -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"you@gmail.com","password":"secret123"}'
# -> check the inbox (and spam) for the 6-digit code

curl -X POST $API/auth/verify-email -H "Content-Type: application/json" \
  -d '{"email":"you@gmail.com","code":"123456"}'
# -> returns access_token + user

curl -X POST $API/auth/forgot-password/start -H "Content-Type: application/json" \
  -d '{"email":"you@gmail.com"}'
curl -X POST $API/auth/forgot-password/verify -H "Content-Type: application/json" \
  -d '{"email":"you@gmail.com","code":"654321","new_password":"newsecret123"}'
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| No email arrives | Custom SMTP not enabled, or sender domain not verified. Check **Authentication -> Logs** in Supabase and your SMTP provider's log. |
| Email arrives with a link, no code | Template still has `{{ .ConfirmationURL }}`; use the templates in step 3. |
| "Too many emails requested" | Supabase allows about 1 email per user per minute; wait, or raise limits. |
| 503 "Email service is not configured" | `SUPABASE_URL` / `SUPABASE_ANON_KEY` missing on the backend. |
| Emails go to spam | Add the SPF/DKIM records your SMTP provider gives you. |
| Code says invalid/expired | Codes expire after an hour by default and only the newest one works. Use "Resend code". |

## Accounts created before this change

Old accounts exist only in your own database, not in Supabase. They can still
log in with their old password (the login endpoint falls back to it), so your
admin account keeps working. They just won't get reset emails until re-created
through the new signup flow.
