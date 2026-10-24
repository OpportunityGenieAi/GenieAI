"""
Environment-driven configuration.
All secrets come from environment variables (see .env.example) — nothing
sensitive is hardcoded, and there is no seeded demo/admin account anywhere
in this codebase. The first admin is created with scripts/make_admin.py.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- core ---
    APP_NAME: str = "OpportunityGenie AI"
    ENVIRONMENT: str = "development"  # development | staging | production

    # --- database ---
    DATABASE_URL: str = "postgresql+psycopg2://og_user:og_pass@localhost:5432/opportunitygenie"

    # --- auth ---
    JWT_SECRET_KEY: str  # REQUIRED — generate with: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14 days

    # --- Supabase Auth (sends signup-confirmation and password-reset emails) ---
    # Project URL and anon/publishable key: Supabase dashboard > Project Settings > API.
    # The anon key is safe here; never put the service_role key in this app.
    SUPABASE_URL: str = ""       # e.g. https://abcdxyz.supabase.co
    SUPABASE_ANON_KEY: str = ""

    # --- AI advisor ---
    # Gemini (free tier via Google AI Studio) is used when GEMINI_API_KEY is set.
    # If GEMINI_MODEL is overloaded or unavailable, GEMINI_FALLBACK_MODEL is tried next.
    # Otherwise the advisor falls back to Anthropic if ANTHROPIC_API_KEY is set.
    # Set these as environment variables on the server (Railway > Variables), never in code.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_FALLBACK_MODEL: str = "gemini-3.1-flash-lite"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # --- Google Play subscriptions (Premium) ---
    GOOGLE_PLAY_PACKAGE_NAME: str = "opportunitygenie.org"
    GOOGLE_PLAY_PRODUCT_ID: str = "premium_monthly"
    GOOGLE_PLAY_SERVICE_ACCOUNT_JSON: str = ""  # the whole service-account key, as one line
    PLAY_RTDN_SECRET: str = ""                  # random string used in the Pub/Sub push URL
    PREMIUM_GATING_STARTS_AT: str = ""          # e.g. 2026-12-01 (UTC); empty = Premium not enforced yet
    PREMIUM_GRACE_DAYS: int = 14                # accounts created before that date keep access this long

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def _fix_db_url(cls, v: str) -> str:
        for old in ("postgres://", "postgresql://"):
            if v.startswith(old):
                return "postgresql+psycopg2://" + v[len(old):]
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
