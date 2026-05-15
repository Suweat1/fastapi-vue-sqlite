from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from . import crud, schemas
from .models import ChatMessage, Conversation, Item, Notification, PurchaseOrder, User
from .realtime import realtime_manager


def _user_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


def _conversation_unread(conversation: Conversation, user_id: int) -> int:
    if conversation.buyer_id == user_id:
        return conversation.unread_buyer_count
    if conversation.seller_id == user_id:
        return conversation.unread_seller_count
    return 0


def _purchase_order_dict(order: PurchaseOrder, item: Item, buyer: User, seller: User) -> dict[str, Any]:
    return {
        "id": order.id,
        "item": crud.item_to_dict(item, favorite_ids=set()),
        "buyer": _user_dict(buyer),
        "seller": _user_dict(seller),
        "amount": float(order.amount),
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _conversation_dict(conversation: Conversation, current_user_id: int) -> dict[str, Any]:
    item_payload = crud.item_to_dict(conversation.item, favorite_ids=set())
    buyer_payload = _user_dict(conversation.buyer)
    seller_payload = _user_dict(conversation.seller)
    other_user = conversation.seller if conversation.buyer_id == current_user_id else conversation.buyer
    return {
        "id": conversation.id,
        "item": item_payload,
        "buyer": buyer_payload,
        "seller": seller_payload,
        "other_user": _user_dict(other_user),
        "last_message_preview": conversation.last_message_preview,
        "last_message_at": conversation.last_message_at,
        "unread_count": _conversation_unread(conversation, current_user_id),
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


def _message_dict(message: ChatMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender": _user_dict(message.sender),
        "content": message.content,
        "created_at": message.created_at,
    }


def _notification_dict(notification: Notification) -> dict[str, Any]:
    item_title = notification.item.title if notification.item else None
    item_cover = notification.item.images[0].url if notification.item and notification.item.images else None
    return {
        "id": notification.id,
        "kind": notification.kind,
        "title": notification.title,
        "content": notification.content,
        "is_read": notification.is_read,
        "item_id": notification.item_id,
        "item_title": item_title,
        "item_cover_image": item_cover,
        "conversation_id": notification.conversation_id,
        "order_id": notification.order_id,
        "created_at": notification.created_at,
    }


def _create_notification(
    session: Session,
    *,
    user_id: int,
    kind: str,
    title: str,
    content: str,
    item_id: int | None = None,
    order_id: int | None = None,
    conversation_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        kind=kind,
        title=title,
        content=content[:255],
        item_id=item_id,
        order_id=order_id,
        conversation_id=conversation_id,
        is_read=False,
    )
    session.add(notification)
    return notification


def _broadcast_user_event(user_id: int, event_type: str, payload: dict[str, Any]) -> None:
    realtime_manager.broadcast(user_id, {"type": event_type, **payload})


def purchase_item(session: Session, buyer: User, item_id: int) -> dict[str, Any]:
    item = crud.get_item(session, item_id, current_user_id=buyer.id, public_only=True)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")
    if item.seller_id == buyer.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能购买自己的物品")
    if item.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该物品已经下架或售出")

    existing_order = session.scalar(select(PurchaseOrder.id).where(PurchaseOrder.item_id == item.id))
    if existing_order:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该物品已被购买")

    order = PurchaseOrder(
        item_id=item.id,
        buyer_id=buyer.id,
        seller_id=item.seller_id,
        amount=Decimal(str(item.price)),
        status="completed",
    )
    item.status = "sold"
    session.add(order)
    session.flush()

    buyer_name = buyer.nickname or buyer.username
    seller_notification = _create_notification(
        session,
        user_id=item.seller_id,
        kind="order",
        title="商品已售出",
        content=f"你的物品《{item.title}》已被 {buyer_name} 购买。",
        item_id=item.id,
        order_id=order.id,
    )
    buyer_notification = _create_notification(
        session,
        user_id=buyer.id,
        kind="order",
        title="购买成功",
        content=f"你已成功购买《{item.title}》，可随时查看订单记录。",
        item_id=item.id,
        order_id=order.id,
    )
    session.commit()
    session.refresh(order)
    session.refresh(seller_notification)
    session.refresh(buyer_notification)
    _broadcast_user_event(seller_notification.user_id, "notification.new", {"notification": _notification_dict(seller_notification)})
    _broadcast_user_event(buyer_notification.user_id, "notification.new", {"notification": _notification_dict(buyer_notification)})
    return _purchase_order_dict(order, item, buyer, item.seller)


def list_orders(session: Session, user_id: int, scope: str = "all", page: int = 1, page_size: int = 12) -> dict[str, Any]:
    stmt = (
        select(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.item).joinedload(Item.seller),
            joinedload(PurchaseOrder.item).joinedload(Item.category),
            joinedload(PurchaseOrder.item).selectinload(Item.images),
            joinedload(PurchaseOrder.buyer),
            joinedload(PurchaseOrder.seller),
        )
        .order_by(desc(PurchaseOrder.created_at), desc(PurchaseOrder.id))
    )
    if scope == "buyer":
        stmt = stmt.where(PurchaseOrder.buyer_id == user_id)
    elif scope == "seller":
        stmt = stmt.where(PurchaseOrder.seller_id == user_id)
    else:
        stmt = stmt.where(or_(PurchaseOrder.buyer_id == user_id, PurchaseOrder.seller_id == user_id))

    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    offset = (page - 1) * page_size
    orders = list(session.scalars(stmt.offset(offset).limit(page_size)).unique().all())
    payload = [_purchase_order_dict(order, order.item, order.buyer, order.seller) for order in orders]
    return {
        "items": payload,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, ceil(total / page_size)) if total else 1,
    }


def get_or_create_conversation(session: Session, user: User, item_id: int) -> dict[str, Any]:
    item = crud.get_item(session, item_id, current_user_id=user.id, public_only=True)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物品不存在")
    if item.seller_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能和自己发起私聊")

    conversation = session.scalar(
        select(Conversation)
        .options(
            joinedload(Conversation.item).joinedload(Item.seller),
            joinedload(Conversation.item).joinedload(Item.category),
            joinedload(Conversation.item).selectinload(Item.images),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
        )
        .where(
            Conversation.item_id == item.id,
            Conversation.buyer_id == user.id,
            Conversation.seller_id == item.seller_id,
        )
    )
    if conversation:
        return _conversation_dict(conversation, user.id)

    conversation = Conversation(
        item_id=item.id,
        buyer_id=user.id,
        seller_id=item.seller_id,
        last_message_preview="",
        last_message_at=datetime.utcnow(),
        unread_buyer_count=0,
        unread_seller_count=0,
    )
    session.add(conversation)
    session.commit()
    conversation = session.scalar(
        select(Conversation)
        .options(
            joinedload(Conversation.item).joinedload(Item.seller),
            joinedload(Conversation.item).joinedload(Item.category),
            joinedload(Conversation.item).selectinload(Item.images),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
        )
        .where(Conversation.id == conversation.id)
    )
    return _conversation_dict(conversation, user.id)


def get_or_create_conversation_from_order(session: Session, user: User, order_id: int) -> dict[str, Any]:
    order = session.scalar(
        select(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.item).joinedload(Item.seller),
            joinedload(PurchaseOrder.item).joinedload(Item.category),
            joinedload(PurchaseOrder.item).selectinload(Item.images),
            joinedload(PurchaseOrder.buyer),
            joinedload(PurchaseOrder.seller),
        )
        .where(PurchaseOrder.id == order_id)
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if user.id not in {order.buyer_id, order.seller_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权发起该会话")

    conversation = session.scalar(
        select(Conversation)
        .options(
            joinedload(Conversation.item).joinedload(Item.seller),
            joinedload(Conversation.item).joinedload(Item.category),
            joinedload(Conversation.item).selectinload(Item.images),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
        )
        .where(
            Conversation.item_id == order.item_id,
            Conversation.buyer_id == order.buyer_id,
            Conversation.seller_id == order.seller_id,
        )
    )
    if conversation:
        return _conversation_dict(conversation, user.id)

    conversation = Conversation(
        item_id=order.item_id,
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        last_message_preview="",
        last_message_at=datetime.utcnow(),
        unread_buyer_count=0,
        unread_seller_count=0,
    )
    session.add(conversation)
    session.commit()
    conversation = session.scalar(
        select(Conversation)
        .options(
            joinedload(Conversation.item).joinedload(Item.seller),
            joinedload(Conversation.item).joinedload(Item.category),
            joinedload(Conversation.item).selectinload(Item.images),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
        )
        .where(Conversation.id == conversation.id)
    )
    return _conversation_dict(conversation, user.id)


def list_conversations(session: Session, user_id: int) -> dict[str, Any]:
    stmt = (
        select(Conversation)
        .options(
            joinedload(Conversation.item).joinedload(Item.seller),
            joinedload(Conversation.item).joinedload(Item.category),
            joinedload(Conversation.item).selectinload(Item.images),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
        )
        .where(or_(Conversation.buyer_id == user_id, Conversation.seller_id == user_id))
        .order_by(desc(Conversation.last_message_at), desc(Conversation.updated_at), desc(Conversation.id))
    )
    conversations = list(session.scalars(stmt).unique().all())
    payload = [_conversation_dict(conversation, user_id) for conversation in conversations]
    return {"items": payload, "total": len(payload)}


def list_messages(session: Session, conversation_id: int, user_id: int) -> dict[str, Any]:
    conversation = session.scalar(
        select(Conversation)
        .options(
            joinedload(Conversation.item).joinedload(Item.seller),
            joinedload(Conversation.item).joinedload(Item.category),
            joinedload(Conversation.item).selectinload(Item.images),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
        )
        .where(Conversation.id == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if user_id not in {conversation.buyer_id, conversation.seller_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该会话")

    messages = list(
        session.scalars(
            select(ChatMessage)
            .options(joinedload(ChatMessage.sender))
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        ).all()
    )
    return {
        "conversation": _conversation_dict(conversation, user_id),
        "items": [_message_dict(message) for message in messages],
        "total": len(messages),
    }


def send_message(session: Session, conversation_id: int, user: User, content: str) -> dict[str, Any]:
    conversation = session.scalar(
        select(Conversation)
        .options(joinedload(Conversation.item), joinedload(Conversation.buyer), joinedload(Conversation.seller))
        .where(Conversation.id == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if user.id not in {conversation.buyer_id, conversation.seller_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权发送消息")

    content = content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="消息内容不能为空")

    message = ChatMessage(conversation_id=conversation.id, sender=user, content=content)
    session.add(message)

    preview = content.replace("\n", " ").strip()
    conversation.last_message_preview = preview[:120]
    conversation.last_message_at = datetime.utcnow()

    if user.id == conversation.buyer_id:
        conversation.unread_seller_count += 1
        recipient_id = conversation.seller_id
    else:
        conversation.unread_buyer_count += 1
        recipient_id = conversation.buyer_id

    sender_name = user.nickname or user.username
    notification = _create_notification(
        session,
        user_id=recipient_id,
        kind="message",
        title="收到新消息",
        content=f"{sender_name} 给你发来了一条新消息。",
        item_id=conversation.item_id,
        conversation_id=conversation.id,
    )

    session.commit()
    session.refresh(message)
    session.refresh(conversation)
    session.refresh(notification)
    message_payload = _message_dict(message)
    sender_conversation = _conversation_dict(conversation, user.id)
    recipient_conversation = _conversation_dict(conversation, recipient_id)
    _broadcast_user_event(
        user.id,
        "message.new",
        {
            "message": message_payload,
            "conversation": sender_conversation,
            "sender_id": user.id,
            "recipient_id": recipient_id,
        },
    )
    _broadcast_user_event(
        recipient_id,
        "message.new",
        {
            "message": message_payload,
            "conversation": recipient_conversation,
            "sender_id": user.id,
            "recipient_id": recipient_id,
        },
    )
    _broadcast_user_event(recipient_id, "notification.new", {"notification": _notification_dict(notification)})
    return message_payload


def mark_conversation_read(session: Session, conversation_id: int, user_id: int) -> dict[str, Any]:
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if user_id not in {conversation.buyer_id, conversation.seller_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该会话")
    if conversation.buyer_id == user_id:
        conversation.unread_buyer_count = 0
    else:
        conversation.unread_seller_count = 0
    session.execute(
        Notification.__table__.update()
        .where(Notification.user_id == user_id, Notification.conversation_id == conversation_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    session.commit()
    conversation_payload = _conversation_dict(conversation, user_id)
    _broadcast_user_event(user_id, "conversation.updated", {"conversation": conversation_payload, "conversation_id": conversation_id})
    _broadcast_user_event(
        user_id,
        "notification.updated",
        {"conversation_id": conversation_id, "unread_count": unread_notification_count(session, user_id)},
    )
    return {"ok": True}


def list_notifications(session: Session, user_id: int, page: int = 1, page_size: int = 12) -> dict[str, Any]:
    stmt = (
        select(Notification)
        .options(selectinload(Notification.item).selectinload(Item.images))
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at), desc(Notification.id))
    )
    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    offset = (page - 1) * page_size
    rows = list(session.scalars(stmt.offset(offset).limit(page_size)).unique().all())
    payload = [_notification_dict(row) for row in rows]
    return {
        "items": payload,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, ceil(total / page_size)) if total else 1,
    }


def unread_notification_count(session: Session, user_id: int) -> int:
    return int(
        session.scalar(select(func.count(Notification.id)).where(Notification.user_id == user_id, Notification.is_read.is_(False)))
        or 0
    )


def mark_notification_read(session: Session, notification_id: int, user_id: int) -> dict[str, Any]:
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    if notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该通知")
    notification.is_read = True
    session.commit()
    _broadcast_user_event(
        user_id,
        "notification.updated",
        {"notification_id": notification_id, "unread_count": unread_notification_count(session, user_id)},
    )
    return {"ok": True}


def mark_all_notifications_read(session: Session, user_id: int) -> dict[str, Any]:
    session.execute(
        Notification.__table__.update()
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    session.commit()
    _broadcast_user_event(
        user_id,
        "notification.updated",
        {"scope": "all", "unread_count": unread_notification_count(session, user_id)},
    )
    return {"ok": True}
