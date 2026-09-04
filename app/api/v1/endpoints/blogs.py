import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.i18n import get_lang_param, localize
from app.api.deps import require_admin
from app.models.content import Blog
from app.schemas.blog import BlogListItem, BlogDetail, BlogCreate

router = APIRouter(prefix="/blogs", tags=["Blog"])


@router.get("", response_model=list[BlogListItem])
def list_blogs(lang: str | None = Depends(get_lang_param), db: Session = Depends(get_db)):
    blogs = db.execute(select(Blog).where(Blog.is_published == True).order_by(Blog.published_at.desc())).scalars()  # noqa: E712
    return [
        BlogListItem(
            id=b.id, title=localize(b.title, lang), slug=b.slug, cover_image=b.cover_image,
            read_time_minutes=b.read_time_minutes, published_at=b.published_at,
        )
        for b in blogs
    ]


@router.get("/{slug}", response_model=BlogDetail)
def get_blog(slug: str, lang: str | None = Depends(get_lang_param), db: Session = Depends(get_db)):
    blog = db.execute(select(Blog).where(Blog.slug == slug)).scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Maqola topilmadi")
    return BlogDetail(
        id=blog.id, title=localize(blog.title, lang), slug=blog.slug, cover_image=blog.cover_image,
        read_time_minutes=blog.read_time_minutes, published_at=blog.published_at,
        content=localize(blog.content, lang),
    )


@router.post("", response_model=BlogDetail, status_code=201, dependencies=[Depends(require_admin)])
def create_blog(data: BlogCreate, db: Session = Depends(get_db)):
    blog = Blog(**data.model_dump())
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return BlogDetail(
        id=blog.id, title=blog.title, slug=blog.slug, cover_image=blog.cover_image,
        read_time_minutes=blog.read_time_minutes, published_at=blog.published_at, content=blog.content,
    )
