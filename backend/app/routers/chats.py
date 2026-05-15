from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import commerce, schemas
from ..deps import get_current_user, get_db


router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/conversations", response_model=schemas.ConversationListResponse)
def list_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.list_conversations(db, current_user.id)


@router.post("/from-item/{item_id}", response_model=schemas.ConversationPublic)
def start_conversation_from_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.get_or_create_conversation(db, current_user, item_id)


@router.post("/from-order/{order_id}", response_model=schemas.ConversationPublic)
def start_conversation_from_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.get_or_create_conversation_from_order(db, current_user, order_id)


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationMessagesResponse)
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = commerce.list_messages(db, conversation_id, current_user.id)
    return {
        "conversation": result["conversation"],
        "items": result["items"],
        "total": result["total"],
    }


@router.post("/conversations/{conversation_id}/messages", response_model=schemas.MessagePublic)
def send_message(
    conversation_id: int,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.send_message(db, conversation_id, current_user, payload.content)


@router.put("/conversations/{conversation_id}/read")
def mark_conversation_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return commerce.mark_conversation_read(db, conversation_id, current_user.id)
