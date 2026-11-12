"""Website articles: public pages + a private API used by /dashboard."""
import base64
import hmac
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.article_model import Article, ArticleImage
from app.database import get_db
from app.services import article_render as R

router = APIRouter()
WEBSITE_DIR = Path(__file__).resolve().parent.parent.parent / "website"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,89}$")


# ---------- admin guard (shared key kept in the ARTICLES_ADMIN_KEY variable) ----------
def require_key(x_admin_key: str = Header(default="")):
    expected = os.environ.get("ARTICLES_ADMIN_KEY", "")
    if len(expected) < 12:
        raise HTTPException(503, "ARTICLES_ADMIN_KEY is not set (or is too short) on the server")
    if not hmac.compare_digest(x_admin_key.encode("utf-8"), expected.encode("utf-8")):
        time.sleep(1)  # slows down guessing
        raise HTTPException(401, "Wrong key")


class FaqItem(BaseModel):
    q: str = Field(default="", max_length=300)
    a: str = Field(default="", max_length=1500)


class ArticleIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    slug: Optional[str] = Field(default=None, max_length=90)
    description: str = Field(default="", max_length=320)
    keyword: str = Field(default="", max_length=120)
    lead: str = Field(default="", max_length=600)
    body: str = Field(default="", max_length=60000)
    faq: List[FaqItem] = []
    status: str = Field(default="draft", max_length=12)


class PreviewIn(BaseModel):
    body: str = Field(default="", max_length=60000)


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ") if d else None


def _image_info(db: Session, article_id: str):
    im = db.query(ArticleImage).filter(ArticleImage.article_id == article_id).first()
    if not im:
        return None
    return {"alt": im.alt or "", "w": im.width or 0, "h": im.height or 0, "v": int(im.updated_at.timestamp()) if im.updated_at else 0}


def _out(a: Article, db: Session) -> dict:
    return {"image": _image_info(db, a.id),
        "id": a.id, "slug": a.slug, "title": a.title, "description": a.description or "", "keyword": a.keyword or "",
        "lead": a.lead or "", "body": a.body or "", "faq": a.faq or [], "status": a.status,
        "published_at": _iso(a.published_at), "updated_at": _iso(a.updated_at),
    }


def _apply(a: Article, p: ArticleIn, db: Session):
    slug = R.slugify(p.slug or p.title)
    if not SLUG_RE.match(slug):
        raise HTTPException(422, "Web address (slug) must use letters, numbers and dashes")
    taken = db.query(Article).filter(Article.slug == slug)
    if a.id:
        taken = taken.filter(Article.id != a.id)
    if taken.first() or any(s["slug"] == slug for s in R.STATIC_ARTICLES):
        raise HTTPException(409, "Another article already uses this web address")
    a.slug, a.title = slug, p.title.strip()
    a.description, a.keyword, a.lead, a.body = p.description.strip(), p.keyword.strip(), p.lead.strip(), p.body
    a.faq = [f.model_dump() if hasattr(f, "model_dump") else f.dict() for f in p.faq if f.q.strip() and f.a.strip()]
    if p.status not in ("draft", "published"):
        raise HTTPException(422, "Status must be draft or published")
    if p.status == "published" and not a.published_at:
        a.published_at = datetime.utcnow()  # first publish date is kept if you unpublish and republish
    a.status = p.status


# ---------- private API ----------
@router.get("/admin-api/articles", dependencies=[Depends(require_key)])
def admin_list(db: Session = Depends(get_db)):
    rows = db.query(Article).order_by(Article.updated_at.desc()).all()
    return [{"id": a.id, "slug": a.slug, "title": a.title, "status": a.status, "updated_at": _iso(a.updated_at)} for a in rows]


@router.post("/admin-api/articles", dependencies=[Depends(require_key)])
def admin_create(p: ArticleIn, db: Session = Depends(get_db)):
    a = Article()
    _apply(a, p, db)
    db.add(a)
    db.commit()
    db.refresh(a)
    return _out(a, db)


@router.post("/admin-api/articles/preview", dependencies=[Depends(require_key)])
def admin_preview(p: PreviewIn):
    return {"html": R.md_to_html(p.body, "preview")}


@router.get("/admin-api/articles/{article_id}", dependencies=[Depends(require_key)])
def admin_get(article_id: str, db: Session = Depends(get_db)):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(404, "Article not found")
    return _out(a, db)


@router.put("/admin-api/articles/{article_id}", dependencies=[Depends(require_key)])
def admin_update(article_id: str, p: ArticleIn, db: Session = Depends(get_db)):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(404, "Article not found")
    _apply(a, p, db)
    db.commit()
    db.refresh(a)
    return _out(a, db)


@router.delete("/admin-api/articles/{article_id}", dependencies=[Depends(require_key)])
def admin_delete(article_id: str, db: Session = Depends(get_db)):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(404, "Article not found")
    db.query(ArticleImage).filter(ArticleImage.article_id == a.id).delete()
    db.delete(a)
    db.commit()
    return {"ok": True}


# ---------- main picture ----------
MAX_IMAGE_BYTES = 1_500_000


class ImageIn(BaseModel):
    data: str = Field(max_length=2_200_000)   # base64, without the "data:" prefix
    alt: str = Field(default="", max_length=200)
    width: int = Field(default=0, ge=0, le=6000)
    height: int = Field(default=0, ge=0, le=6000)


class AltIn(BaseModel):
    alt: str = Field(default="", max_length=200)


def _sniff(raw: bytes):
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


@router.put("/admin-api/articles/{article_id}/image", dependencies=[Depends(require_key)])
def admin_set_image(article_id: str, p: ImageIn, db: Session = Depends(get_db)):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(404, "Article not found")
    try:
        raw = base64.b64decode(p.data, validate=True)
    except Exception:
        raise HTTPException(422, "The picture could not be read")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Picture is too large (limit 1.5 MB)")
    ctype = _sniff(raw)
    if not ctype:
        raise HTTPException(422, "Use a JPG, PNG or WebP picture")
    im = db.query(ArticleImage).filter(ArticleImage.article_id == a.id).first() or ArticleImage(article_id=a.id)
    im.content_type, im.data, im.alt, im.width, im.height = ctype, raw, p.alt.strip(), p.width, p.height
    im.updated_at = datetime.utcnow()
    db.add(im)
    db.commit()
    return _out(a, db)


@router.put("/admin-api/articles/{article_id}/image-alt", dependencies=[Depends(require_key)])
def admin_set_alt(article_id: str, p: AltIn, db: Session = Depends(get_db)):
    im = db.query(ArticleImage).filter(ArticleImage.article_id == article_id).first()
    if not im:
        raise HTTPException(404, "This article has no picture")
    im.alt = p.alt.strip()
    db.commit()
    return {"ok": True}


@router.delete("/admin-api/articles/{article_id}/image", dependencies=[Depends(require_key)])
def admin_delete_image(article_id: str, db: Session = Depends(get_db)):
    db.query(ArticleImage).filter(ArticleImage.article_id == article_id).delete()
    db.commit()
    return {"ok": True}


@router.get("/article-image/{article_id}", include_in_schema=False)
def article_image(article_id: str, db: Session = Depends(get_db)):
    im = db.query(ArticleImage).filter(ArticleImage.article_id == article_id).first()
    if not im:
        raise HTTPException(404, "Not found")
    return Response(bytes(im.data), media_type=im.content_type, headers={"Cache-Control": "public, max-age=604800"})


# ---------- public pages ----------
CACHE = {"Cache-Control": "public, max-age=300"}


def _published(db: Session):
    return db.query(Article).filter(Article.status == "published").order_by(Article.published_at.desc()).all()


@router.get("/articles/", response_class=HTMLResponse, include_in_schema=False)
def articles_index(db: Session = Depends(get_db)):
    items = [{"slug": a.slug, "title": a.title, "description": a.description} for a in _published(db)]
    items += R.STATIC_ARTICLES
    return HTMLResponse(R.index_page(items), headers=CACHE)


@router.get("/articles/{slug}/", response_class=HTMLResponse, include_in_schema=False)
def article_view(slug: str, db: Session = Depends(get_db)):
    a = db.query(Article).filter(Article.slug == slug, Article.status == "published").first()
    if a:
        return HTMLResponse(R.article_page(_out(a, db)), headers=CACHE)
    if SLUG_RE.match(slug):
        f = WEBSITE_DIR / "articles" / slug / "index.html"
        if f.is_file():
            return FileResponse(str(f), media_type="text/html", headers=CACHE)
    return HTMLResponse(R.not_found_page(), status_code=404)


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)):
    entries = [(u, None) for u in R.STATIC_URLS]
    entries += [(f"/articles/{a.slug}/", (a.updated_at or a.published_at or datetime.utcnow()).strftime("%Y-%m-%d")) for a in _published(db)]
    return Response(R.sitemap_xml(entries), media_type="application/xml", headers=CACHE)
