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

    # --- AI advisor (Anthropic) ---
    ANTHROPIC_API_KEY: str = ""  # REQUIRED to enable the AI advisor endpoint
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # --- billing (Stripe) — required only once you enable subscriptions ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PREMIUM: str = ""
    BILLING_SUCCESS_URL: str = "https://your-domain.example.com/billing/success"
    BILLING_CANCEL_URL: str = "https://your-domain.example.com/billing/cancel"

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
