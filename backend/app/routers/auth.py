from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..deps import get_current_user, get_db
from ..security import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    if payload.email and crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")
    user = crud.create_user(db, payload)
    token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})
    return schemas.Token(access_token=token)


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserPublic)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserPublic)
def update_me(
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.email and payload.email != current_user.email:
        existing = crud.get_user_by_email(db, payload.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已存在")
    return crud.update_user(db, current_user, payload)

