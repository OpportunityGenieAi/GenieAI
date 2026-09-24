"""
Thin client for Supabase Auth (GoTrue) REST API.

Supabase owns the parts that need email: it sends the signup confirmation
code and the password-reset code (via the SMTP provider configured in the
Supabase dashboard). This module only calls its public endpoints with the
anon key, so no service-role key is ever needed.
"""
import httpx
from fastapi import HTTPException

from app.config import settings


class SupabaseAuthError(HTTPException):
    """HTTPException that also remembers Supabase's machine-readable error code."""

    def __init__(self, status_code: int, detail: str, error_code: str = ""):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


# Supabase error_code -> (http status, message shown to the user)
_FRIENDLY = {
    "invalid_credentials": (401, "That email and password don't match our records."),
    "email_not_confirmed": (403, "Please verify your email first. Enter the code we sent you."),
    "otp_expired": (400, "That code is invalid or has expired. Request a new one."),
    "over_email_send_rate_limit": (429, "Too many emails requested. Please wait a minute and try again."),
    "over_request_rate_limit": (429, "Too many attempts. Please wait a minute and try again."),
    "weak_password": (422, "Choose a stronger password."),
    "same_password": (422, "Your new password must be different from the old one."),
    "user_already_exists": (409, "An account with that email already exists."),
    "email_exists": (409, "An account with that email already exists."),
    "signup_disabled": (503, "Sign-ups are currently disabled."),
    "validation_failed": (422, "That doesn't look right. Please check what you entered."),
}


def _call(method: str, path: str, *, json=None, params=None, bearer: str | None = None) -> dict:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise SupabaseAuthError(503, "Email service is not configured yet.", "not_configured")

    headers = {"apikey": settings.SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    try:
        res = httpx.request(
            method,
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1{path}",
            json=json, params=params, headers=headers, timeout=15.0,
        )
    except httpx.HTTPError:
        raise SupabaseAuthError(503, "Couldn't reach the email service. Please try again.", "unreachable")

    if res.is_success:
        return res.json() if res.content else {}

    try:
        body = res.json()
    except ValueError:
        body = {}
    error_code = str(body.get("error_code") or "")
    if error_code in _FRIENDLY:
        status, message = _FRIENDLY[error_code]
    elif res.status_code == 429:
        status, message = 429, "Too many attempts. Please wait a minute and try again."
    else:
        status = 400
        message = body.get("msg") or body.get("message") or "Something went wrong. Please try again."
    raise SupabaseAuthError(status, message, error_code)


def sign_up(email: str, password: str, name: str) -> None:
    """Creates the user in Supabase and emails the confirmation code."""
    _call("POST", "/signup", json={"email": email, "password": password, "data": {"name": name}})


def resend_signup_code(email: str) -> None:
    _call("POST", "/resend", json={"type": "signup", "email": email})


def verify_code(email: str, code: str, kind: str) -> dict:
    """kind = 'signup' (confirm email) or 'recovery' (password reset). Returns the session."""
    return _call("POST", "/verify", json={"type": kind, "email": email, "token": code.strip()})


def sign_in(email: str, password: str) -> dict:
    return _call("POST", "/token", params={"grant_type": "password"}, json={"email": email, "password": password})


def send_recovery_code(email: str) -> None:
    _call("POST", "/recover", json={"email": email})


def update_password(access_token: str, new_password: str) -> None:
    _call("PUT", "/user", json={"password": new_password}, bearer=access_token)
