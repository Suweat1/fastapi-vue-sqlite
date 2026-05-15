from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..deps import get_current_user, get_db
from ..models import Item


router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=schemas.ItemListResponse)
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    q: str | None = None,
    category_id: int | None = None,
    sort: str = Query(default="newest"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.list_favorites(db, user_id=current_user.id, page=page, page_size=page_size, q=q, category_id=category_id, sort=sort)


@router.post("/{item_id}/toggle", response_model=schemas.FavoriteToggleResponse)
def toggle_favorite(item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")
    favorited, favorite_count = crud.toggle_favorite(db, current_user.id, item_id)
    return schemas.FavoriteToggleResponse(item_id=item_id, favorited=favorited, favorite_count=favorite_count)

