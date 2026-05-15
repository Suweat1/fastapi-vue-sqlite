from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import commerce, schemas
from ..deps import get_current_user, get_db


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/purchase/{item_id}", response_model=schemas.PurchaseOrderPublic)
def purchase_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.purchase_item(db, current_user, item_id)


@router.get("/me", response_model=schemas.PurchaseOrderListResponse)
def list_my_orders(
    scope: str = Query(default="all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if scope not in {"all", "buyer", "seller"}:
        scope = "all"
    return commerce.list_orders(db, current_user.id, scope=scope, page=page, page_size=page_size)
