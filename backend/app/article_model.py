from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models import gen_uuid


class Article(Base):
    """A website article written in the /dashboard page."""

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, default="")   # meta description shown on Google
    keyword = Column(String, default="")       # main search keyword (for your reference)
    lead = Column(Text, default="")            # short intro under the title
    body = Column(Text, default="")            # simple Markdown
    faq = Column(JSON, default=list)           # [{"q": "...", "a": "..."}]
    status = Column(String, default="draft", index=True)  # draft | published
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArticleImage(Base):
    """The main picture shown above an article's introduction (one per article)."""

    __tablename__ = "article_images"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    article_id = Column(UUID(as_uuid=False), ForeignKey("articles.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    content_type = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)
    alt = Column(String, default="")
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
