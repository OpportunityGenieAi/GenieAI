from fastapi import FastAPI
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
    db = SessionLocal()
    try:
        if db.query(Scholarship).count() == 0:
            db.bulk_insert_mappings(Scholarship, SEED_SCHOLARSHIPS)
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
