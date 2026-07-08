import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, verify_qdrant, get_qdrant_client
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import KbArticle

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize(art: KbArticle) -> Dict[str, Any]:
    return {
        "id": art.id,
        "title": art.title,
        "category": art.category,
        "views": art.views,
        "created_at": art.created_at.isoformat() if art.created_at else None,
        "updated_at": art.updated_at.isoformat() if art.updated_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_articles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(KbArticle)
        .where(KbArticle.organization_id == current_user.organization_id)
        .order_by(KbArticle.title.asc())
    )
    res = await db.execute(query)
    items = res.scalars().all()
    return {"articles": [_serialize(a) for a in items]}


class KbArticleCreateBody(BaseModel):
    title: str
    category: str


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_article(
    body: KbArticleCreateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    art = KbArticle(
        organization_id=current_user.organization_id,
        title=body.title.strip(),
        category=body.category.strip(),
        views=0,
    )
    db.add(art)
    await db.commit()
    await db.refresh(art)

    # If Qdrant is connected, we can upsert index
    try:
        from app.core.qdrant_vector import upsert_kb_article_vector
        await upsert_kb_article_vector(art.id, art.title, art.category)
    except Exception as e:
        logger.warning(f"Failed Qdrant upload: {e}")

    return _serialize(art)


@router.delete("/{article_id}", response_model=Dict[str, Any])
async def delete_article(
    article_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    art = await db.get(KbArticle, article_id)
    if not art or art.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(art)
    await db.commit()
    return {"success": True}


@router.get("/search", response_model=Dict[str, Any])
async def search_articles(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Executes keyword-based search on the database or fallback semantic search."""
    # Database pattern matching
    like_query = f"%{q}%"
    stmt = (
        select(KbArticle)
        .where(
            KbArticle.organization_id == current_user.organization_id,
            (KbArticle.title.ilike(like_query) | KbArticle.category.ilike(like_query))
        )
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    return {"results": [_serialize(a) for a in items]}
