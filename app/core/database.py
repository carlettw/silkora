from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


def _clean_url_for_psycopg2(url: str) -> str:
    """
    psycopg2 'pgbouncer=true' kabi query paramni tushunmaydi (bu param asyncpg/prisma
    kabi boshqa drayverlar uchun mo'ljallangan Supabase hint'i). Uni olib tashlaymiz.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query.pop("pgbouncer", None)
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


# pool_pre_ping: pgbouncer/Supabase pooler orqali "stale" ulanishlarni avtomatik yangilaydi
engine = create_engine(_clean_url_for_psycopg2(settings.DATABASE_URL), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: har bir so'rov uchun DB session ochadi va yopadi."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
