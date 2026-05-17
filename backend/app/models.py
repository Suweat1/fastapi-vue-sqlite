from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    items: Mapped[list["Item"]] = relationship(back_populates="seller", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    items: Mapped[list["Item"]] = relationship(back_populates="category")


class Item(Base, TimestampMixin):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_items_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    condition: Mapped[str] = mapped_column(String(30), nullable=False, default="九成新")
    location: Mapped[str] = mapped_column(String(120), nullable=False, default="校园")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)

    seller: Mapped["User"] = relationship(back_populates="items")
    category: Mapped["Category"] = relationship(back_populates="items")
    images: Mapped[list["ItemImage"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemImage.sort_order"
    )
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    view_logs: Mapped[list["ItemView"]] = relationship(back_populates="item", cascade="all, delete-orphan")


class ItemImage(Base, TimestampMixin):
    __tablename__ = "item_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item: Mapped["Item"] = relationship(back_populates="images")


class ItemView(Base, TimestampMixin):
    __tablename__ = "item_views"
    __table_args__ = (UniqueConstraint("item_id", "viewer_key", name="uq_item_view_item_viewer"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    viewer_key: Mapped[str] = mapped_column(String(128), nullable=False)

    item: Mapped["Item"] = relationship(back_populates="view_logs")


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("item_id", name="uq_purchase_orders_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")

    item: Mapped["Item"] = relationship()
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("item_id", "buyer_id", "seller_id", name="uq_conversations_triplet"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_message_preview: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unread_buyer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unread_seller_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item: Mapped["Item"] = relationship()
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conversation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    item: Mapped["Item | None"] = relationship()
    order: Mapped["PurchaseOrder | None"] = relationship()
    conversation: Mapped["Conversation | None"] = relationship()


class Favorite(Base, TimestampMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_user_item_favorite"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="favorites")
    item: Mapped["Item"] = relationship(back_populates="favorites")
