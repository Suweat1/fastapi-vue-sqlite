from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(APIModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(APIModel):
    username: str
    email: str | None = None
    nickname: str = ""


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(APIModel):
    username: str
    password: str


class UserUpdate(APIModel):
    email: str | None = None
    nickname: str | None = None
    password: str | None = Field(default=None, min_length=6)


class UserRoleUpdate(APIModel):
    role: str


class UserPublic(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime


class CategoryBase(APIModel):
    name: str
    slug: str
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(APIModel):
    name: str | None = None
    slug: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryPublic(CategoryBase):
    id: int
    created_at: datetime


class ItemImagePublic(APIModel):
    id: int
    url: str
    sort_order: int


class ItemBase(APIModel):
    title: str
    description: str
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    condition: str = "九成新"
    location: str = "校园"
    status: str = "active"
    category_id: int
    image_urls: list[str] = Field(default_factory=list)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(APIModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    condition: str | None = None
    location: str | None = None
    status: str | None = None
    category_id: int | None = None
    image_urls: list[str] | None = None


class BatchItemUpdate(APIModel):
    item_ids: list[int] = Field(min_length=1)
    status: str | None = None
    category_id: int | None = None
    condition: str | None = None
    is_featured: bool | None = None


class BatchUpdateResult(APIModel):
    updated_count: int


class ItemSellerPublic(UserPublic):
    pass


class ItemPublic(APIModel):
    id: int
    title: str
    description: str
    price: float
    condition: str
    location: str
    status: str
    views: int
    is_featured: bool
    is_favorite: bool = False
    created_at: datetime
    updated_at: datetime
    seller: UserPublic
    category: CategoryPublic
    images: list[ItemImagePublic] = Field(default_factory=list)
    cover_image: str | None = None


class ItemListResponse(APIModel):
    items: list[ItemPublic]
    total: int
    page: int
    page_size: int
    pages: int


class FavoriteToggleResponse(APIModel):
    item_id: int
    favorited: bool
    favorite_count: int


class DashboardStats(APIModel):
    users: int
    items: int
    active_items: int
    sold_items: int
    hidden_items: int
    favorites: int
    views: int
    categories: int
    orders: int
    conversations: int
    messages: int
    notifications: int
    unread_notifications: int
    active_rate: float
    top_items: list[ItemPublic] = Field(default_factory=list)
    category_breakdown: list[dict[str, int | str]] = Field(default_factory=list)


class PaginatedItemsQuery(APIModel):
    page: int = 1
    page_size: int = 12
    q: str | None = None
    category_id: int | None = None
    min_price: float | None = None
    max_price: float | None = None
    condition: str | None = None
    status: str | None = None
    sort: str = "newest"


T = TypeVar("T")


class PaginatedResponse(APIModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class PurchaseOrderPublic(APIModel):
    id: int
    item: ItemPublic
    buyer: UserPublic
    seller: UserPublic
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(APIModel):
    items: list[PurchaseOrderPublic]
    total: int
    page: int
    page_size: int
    pages: int


class MessagePublic(APIModel):
    id: int
    conversation_id: int
    sender: UserPublic
    content: str
    created_at: datetime


class MessageListResponse(APIModel):
    items: list[MessagePublic]
    total: int


class ConversationMessagesResponse(APIModel):
    conversation: ConversationPublic
    items: list[MessagePublic]
    total: int


class ConversationPublic(APIModel):
    id: int
    item: ItemPublic
    buyer: UserPublic
    seller: UserPublic
    other_user: UserPublic
    last_message_preview: str
    last_message_at: datetime | None = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(APIModel):
    items: list[ConversationPublic]
    total: int


class ConversationCreate(APIModel):
    item_id: int


class MessageCreate(APIModel):
    content: str = Field(min_length=1, max_length=1000)


class NotificationPublic(APIModel):
    id: int
    kind: str
    title: str
    content: str
    is_read: bool
    item_id: int | None = None
    item_title: str | None = None
    item_cover_image: str | None = None
    conversation_id: int | None = None
    order_id: int | None = None
    created_at: datetime


class NotificationListResponse(APIModel):
    items: list[NotificationPublic]
    total: int
    page: int
    page_size: int
    pages: int


class NotificationCountResponse(APIModel):
    unread_count: int


class PriceCategoryAvg(APIModel):
    name: str
    count: int
    avg_price: float
    min_price: float
    max_price: float


class PriceDistributionBucket(APIModel):
    range: str
    count: int
    percent: float


class DailyTrendPoint(APIModel):
    date: str
    count: int


class PriceStatsResponse(APIModel):
    category_avg: list[PriceCategoryAvg]
    price_distribution: list[PriceDistributionBucket]
    daily_trend: list[DailyTrendPoint]
