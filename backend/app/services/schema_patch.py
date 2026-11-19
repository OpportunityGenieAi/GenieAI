"""Adds new optional columns to existing tables on startup (safe to run every time)."""
from sqlalchemy import text

from app.database import SessionLocal


def ensure_columns() -> None:
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE scholarships ADD COLUMN IF NOT EXISTS funding_amount VARCHAR"))
        db.commit()
    except Exception as e:  # e.g. brand-new database: create_all makes the column instead
        db.rollback()
        print("schema_patch skipped:", e)
    finally:
        db.close()
