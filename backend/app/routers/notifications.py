from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import commerce, schemas
from ..deps import get_current_user, get_db


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=schemas.NotificationListResponse)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.list_notifications(db, current_user.id, page=page, page_size=page_size)


@router.get("/unread-count", response_model=schemas.NotificationCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {"unread_count": commerce.unread_notification_count(db, current_user.id)}


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.mark_notification_read(db, notification_id, current_user.id)


@router.put("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.mark_all_notifications_read(db, current_user.id)
