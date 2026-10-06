from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Scholarship
from app.routers import advisor, auth, billing, profile, scholarships, tracker
from app.routers import settings as settings_router
from app.seed_data import SEED_SCHOLARSHIPS

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )
    
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(scholarships.router)
app.include_router(profile.router)
app.include_router(tracker.router)
app.include_router(advisor.router)
app.include_router(billing.router)
app.include_router(settings_router.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # Supabase now owns passwords, so the old credential columns must allow NULL.
    # create_all() never alters existing tables, hence this idempotent step.
    try:
        with engine.begin() as conn:
            for col in ("password_hash", "security_question", "security_answer_hash"):
                conn.execute(text(f"ALTER TABLE users ALTER COLUMN {col} DROP NOT NULL"))
    except Exception as exc:  # non-Postgres or table not ready; safe to skip
        print(f"[startup] skipped users column relax: {exc}")

    # Add catalog columns to the existing scholarships table (idempotent, Postgres).
    for ddl in (
        "ALTER TABLE scholarships ADD COLUMN IF NOT EXISTS source_url VARCHAR",
        "ALTER TABLE scholarships ADD COLUMN IF NOT EXISTS deadline_date DATE",
        "ALTER TABLE scholarships ADD COLUMN IF NOT EXISTS last_verified DATE",
        "ALTER TABLE scholarships ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
    ):
        try:
            with engine.begin() as conn:
                conn.execute(text(ddl))
        except Exception as exc:
            print(f"[startup] skipped scholarships column add: {exc}")
    db = SessionLocal()
    try:
        if db.query(Scholarship).count() == 0:
            db.bulk_insert_mappings(Scholarship, SEED_SCHOLARSHIPS)
            db.commit()
    finally:
        db.close()

    # Load curated scholarship batches from app/data/*.csv (idempotent)
    try:
        from app.services.catalog_import import import_catalog
        db = SessionLocal()
        try:
            import_catalog(db)
        finally:
            db.close()
    except Exception as exc:  # a bad CSV must never stop the API booting
        print(f"[catalog] import skipped: {exc}")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
