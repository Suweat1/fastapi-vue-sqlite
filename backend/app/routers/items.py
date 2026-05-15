from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..deps import get_current_user, get_current_user_optional, get_db
from ..models import Item


router = APIRouter(prefix="/items", tags=["items"])
logger = logging.getLogger(__name__)


@router.get("", response_model=schemas.ItemListResponse)
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    q: str | None = None,
    category_id: int | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    condition: str | None = None,
    status_: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="newest"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    result = crud.list_items(
        db,
        page=page,
        page_size=page_size,
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        status=status_,
        sort=sort,
        current_user_id=current_user.id if current_user else None,
        public_only=True,
    )
    return result


@router.get("/me/list", response_model=schemas.ItemListResponse)
def my_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    q: str | None = None,
    status_: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="newest"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.list_my_items(db, user_id=current_user.id, page=page, page_size=page_size, q=q, status=status_, sort=sort)


@router.get("/recommendations/hot", response_model=list[schemas.ItemPublic])
def hot_items(db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    result = crud.list_items(
        db,
        page=1,
        page_size=6,
        sort="hot",
        current_user_id=current_user.id if current_user else None,
    )
    return result["items"]


@router.get("/{item_id}", response_model=schemas.ItemPublic)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
    view_session: str | None = Header(default=None, alias="X-View-Session"),
):
    item = crud.get_item(db, item_id, current_user_id=current_user.id if current_user else None, public_only=True)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")

    viewer_key = view_session.strip() if view_session else None
    item = crud.increment_item_views(db, item, viewer_key=viewer_key)
    favorite = crud.is_favorite(db, current_user.id if current_user else None, item.id)
    return crud.item_to_dict(item, favorite_ids={item.id} if favorite else set())


@router.post("", response_model=schemas.ItemPublic)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        item = crud.create_item(db, current_user.id, payload)
        return crud.item_to_dict(item, favorite_ids=set())
    except HTTPException:
        raise
    except DataError as exc:
        db.rollback()
        logger.exception("Invalid price while creating item for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="价格超出系统支持范围，请将价格控制在 0 - 99999999.99 之间",
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Failed to create item for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="发布失败，请检查分类、价格和图片信息",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error while creating item for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发布失败，请稍后重试",
        ) from exc


@router.put("/{item_id}", response_model=schemas.ItemPublic)
def update_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        item = db.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")
        if item.seller_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该物品")
        item = crud.update_item(db, item, payload)
        return crud.item_to_dict(item, favorite_ids=set())
    except HTTPException:
        raise
    except DataError as exc:
        db.rollback()
        logger.exception("Invalid price while updating item %s for user %s", item_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="价格超出系统支持范围，请将价格控制在 0 - 99999999.99 之间",
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Failed to update item %s for user %s", item_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="保存失败，请检查分类、价格和图片信息",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error while updating item %s for user %s", item_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="保存失败，请稍后重试",
        ) from exc


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")
    if item.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该物品")
    crud.delete_item(db, item)
    return None
