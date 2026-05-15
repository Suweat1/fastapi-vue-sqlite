from __future__ import annotations

from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, reporting, schemas
from ..deps import get_db, require_admin
from ..models import Item, User


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[schemas.UserPublic])
def list_users(db: Session = Depends(get_db)):
    return list(db.query(User).order_by(User.created_at.desc()).all())


@router.patch("/users/{user_id}/role", response_model=schemas.UserPublic)
def update_user_role(user_id: int, payload: schemas.UserRoleUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/items", response_model=schemas.ItemListResponse)
def list_all_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    q: str | None = None,
    category_id: int | None = None,
    status_: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="newest"),
    db: Session = Depends(get_db),
):
    return crud.list_items(
        db,
        page=page,
        page_size=page_size,
        q=q,
        category_id=category_id,
        status=status_,
        sort=sort,
        public_only=False,
    )


@router.patch("/items/{item_id}/status", response_model=schemas.ItemPublic)
def update_item_status(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")
    item = crud.update_item(db, item, payload)
    return crud.item_to_dict(item, favorite_ids=set())


@router.post("/items/batch", response_model=schemas.BatchUpdateResult)
def batch_update_items(payload: schemas.BatchItemUpdate, db: Session = Depends(get_db)):
    """批量修改物品：状态、分类、成色、推荐标记"""
    try:
        updated = crud.batch_update_items(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return schemas.BatchUpdateResult(updated_count=updated)


@router.get("/dashboard/export")
def export_dashboard(db: Session = Depends(get_db)):
    payload, filename = reporting.build_dashboard_export(db)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return StreamingResponse(iter([payload]), media_type="application/zip", headers=headers)
