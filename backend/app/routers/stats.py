from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..deps import get_db, get_current_user_optional


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    return crud.dashboard_stats(db, current_user_id=current_user.id if current_user else None)


@router.get("/prices", response_model=schemas.PriceStatsResponse)
def prices(db: Session = Depends(get_db)):
    return crud.price_stats(db)

