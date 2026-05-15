from __future__ import annotations

from decimal import Decimal
from math import ceil
from pathlib import Path
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from .config import settings
from .models import ChatMessage, Category, Conversation, Favorite, Item, ItemImage, ItemView, Notification, PurchaseOrder, User
from .schemas import (
    CategoryCreate,
    CategoryUpdate,
    ItemCreate,
    ItemPublic,
    ItemUpdate,
    UserCreate,
    UserUpdate,
)
from .security import hash_password, verify_password


DEFAULT_CATEGORIES = [
    ("教材书籍", "books"),
    ("电子数码", "digital"),
    ("生活用品", "daily"),
    ("服饰鞋包", "fashion"),
    ("运动器材", "sports"),
    ("家具家电", "home"),
    ("美妆护理", "beauty"),
    ("其他", "other"),
]


def ensure_default_categories(session: Session) -> None:
    if session.execute(select(func.count(Category.id))).scalar_one() > 0:
        return
    for index, (name, slug) in enumerate(DEFAULT_CATEGORIES):
        session.add(Category(name=name, slug=slug, sort_order=index, is_active=True))
    session.commit()


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def create_user(session: Session, payload: UserCreate) -> User:
    user = User(
        username=payload.username.strip(),
        email=payload.email.strip() if payload.email else None,
        nickname=payload.nickname.strip() or payload.username.strip(),
        password_hash=hash_password(payload.password),
        role="user",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, user: User, payload: UserUpdate) -> User:
    if payload.email is not None:
        user.email = payload.email.strip() or None
    if payload.nickname is not None:
        user.nickname = payload.nickname.strip() or user.nickname
    if payload.password:
        user.password_hash = hash_password(payload.password)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(session, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def list_categories(session: Session, include_inactive: bool = False) -> list[Category]:
    stmt = select(Category).order_by(Category.sort_order.asc(), Category.name.asc())
    if not include_inactive:
        stmt = stmt.where(Category.is_active.is_(True))
    return list(session.scalars(stmt).all())


def create_category(session: Session, payload: CategoryCreate) -> Category:
    category = Category(**payload.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_category(session: Session, category: Category, payload: CategoryUpdate) -> Category:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(category, key, value)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category: Category) -> None:
    session.delete(category)
    session.commit()


def _base_item_query(current_user: User | None = None, public_only: bool = True):
    stmt = select(Item).options(joinedload(Item.seller), joinedload(Item.category), selectinload(Item.images))
    if public_only:
        stmt = stmt.where(Item.status != "hidden")
    return stmt


def _apply_item_filters(stmt, *, q: str | None, category_id: int | None, min_price: float | None, max_price: float | None, condition: str | None, status: str | None, seller_id: int | None):
    if seller_id is not None:
        stmt = stmt.where(Item.seller_id == seller_id)
    if status:
        stmt = stmt.where(Item.status == status)
    elif seller_id is None:
        stmt = stmt.where(Item.status.in_(["active", "sold"]))
    if category_id:
        stmt = stmt.where(Item.category_id == category_id)
    if condition:
        stmt = stmt.where(Item.condition == condition)
    if min_price is not None:
        stmt = stmt.where(Item.price >= Decimal(str(min_price)))
    if max_price is not None:
        stmt = stmt.where(Item.price <= Decimal(str(max_price)))
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.join(Category).where(
            or_(
                Item.title.ilike(keyword),
                Item.description.ilike(keyword),
                Category.name.ilike(keyword),
            )
        )
    return stmt


def _sort_item_query(stmt, sort: str):
    mapping = {
        "newest": [Item.created_at.desc(), Item.id.desc()],
        "oldest": [Item.created_at.asc(), Item.id.asc()],
        "price_asc": [Item.price.asc(), Item.id.desc()],
        "price_desc": [Item.price.desc(), Item.id.desc()],
        "views_desc": [Item.views.desc(), Item.id.desc()],
        "hot": [Item.views.desc(), Item.is_featured.desc(), Item.created_at.desc()],
    }
    order_by = mapping.get(sort, mapping["newest"])
    return stmt.order_by(None).order_by(*order_by)


def _count_pages(total: int, page_size: int) -> int:
    return max(1, ceil(total / page_size)) if total else 1


def _favorite_ids(session: Session, user_id: int | None, item_ids: list[int]) -> set[int]:
    if not user_id or not item_ids:
        return set()
    rows = session.execute(
        select(Favorite.item_id).where(Favorite.user_id == user_id, Favorite.item_id.in_(item_ids))
    ).all()
    return {row[0] for row in rows}


def is_favorite(session: Session, user_id: int | None, item_id: int) -> bool:
    if not user_id:
        return False
    return bool(
        session.scalar(
            select(Favorite.id).where(Favorite.user_id == user_id, Favorite.item_id == item_id)
        )
    )


def item_to_dict(item: Item, *, favorite_ids: set[int] | None = None) -> dict[str, Any]:
    images = list(item.images or [])
    cover = images[0].url if images else None
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "price": float(item.price),
        "condition": item.condition,
        "location": item.location,
        "status": item.status,
        "views": item.views,
        "is_featured": item.is_featured,
        "is_favorite": bool(favorite_ids and item.id in favorite_ids),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "seller": {
            "id": item.seller.id,
            "username": item.seller.username,
            "email": item.seller.email,
            "nickname": item.seller.nickname,
            "role": item.seller.role,
            "is_active": item.seller.is_active,
            "created_at": item.seller.created_at,
        },
        "category": {
            "id": item.category.id,
            "name": item.category.name,
            "slug": item.category.slug,
            "sort_order": item.category.sort_order,
            "is_active": item.category.is_active,
            "created_at": item.category.created_at,
        },
        "images": [
            {"id": image.id, "url": image.url, "sort_order": image.sort_order}
            for image in images
        ],
        "cover_image": cover,
    }


def list_items(
    session: Session,
    *,
    page: int,
    page_size: int,
    q: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    status: str | None = None,
    sort: str = "newest",
    seller_id: int | None = None,
    current_user_id: int | None = None,
    public_only: bool = True,
) -> dict[str, Any]:
    stmt = _base_item_query(public_only=public_only)
    stmt = _apply_item_filters(
        stmt,
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        status=status,
        seller_id=seller_id,
    )
    stmt = _sort_item_query(stmt, sort)
    total = session.scalar(select(func.count()).select_from(stmt.subquery()))
    total = int(total or 0)
    offset = (page - 1) * page_size
    items = list(session.scalars(stmt.offset(offset).limit(page_size)).unique().all())
    favorite_ids = _favorite_ids(session, current_user_id, [item.id for item in items])
    payload = [item_to_dict(item, favorite_ids=favorite_ids) for item in items]
    return {
        "items": payload,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": _count_pages(total, page_size),
    }


def get_item(session: Session, item_id: int, *, current_user_id: int | None = None, public_only: bool = True) -> Item | None:
    stmt = _base_item_query(public_only=public_only).where(Item.id == item_id)
    item = session.scalar(stmt)
    if not item:
        return None
    if current_user_id:
        _ = current_user_id
    return item


def create_item(session: Session, owner_id: int, payload: ItemCreate) -> Item:
    item = Item(
        title=payload.title.strip(),
        description=payload.description.strip(),
        price=Decimal(str(payload.price)),
        condition=payload.condition.strip(),
        location=payload.location.strip(),
        status=payload.status or "active",
        seller_id=owner_id,
        category_id=payload.category_id,
    )
    session.add(item)
    session.flush()
    for index, url in enumerate(payload.image_urls):
        session.add(ItemImage(item_id=item.id, url=url, sort_order=index))
    session.commit()
    session.refresh(item)
    return item


def update_item(session: Session, item: Item, payload: ItemUpdate) -> Item:
    data = payload.model_dump(exclude_unset=True)
    image_urls = data.pop("image_urls", None)
    for key, value in data.items():
        if key == "price" and value is not None:
            setattr(item, key, Decimal(str(value)))
        elif value is not None:
            setattr(item, key, value)
    if image_urls is not None:
        item.images.clear()
        session.flush()
        for index, url in enumerate(image_urls):
            session.add(ItemImage(item_id=item.id, url=url, sort_order=index))
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, item: Item) -> None:
    session.delete(item)
    session.commit()


def batch_update_items(session: Session, payload: "BatchItemUpdate") -> int:
    """批量修改物品属性，返回实际更新的记录数"""
    from .schemas import BatchItemUpdate

    items = session.execute(select(Item).where(Item.id.in_(payload.item_ids))).scalars().all()
    found_ids = {item.id for item in items}
    if len(found_ids) != len(payload.item_ids):
        missing = set(payload.item_ids) - found_ids
        raise ValueError(f"以下物品不存在: {missing}")

    data = payload.model_dump(exclude={"item_ids"}, exclude_unset=True)
    if not data:
        return 0

    updated = 0
    for item in items:
        for key, value in data.items():
            setattr(item, key, value)
        updated += 1

    session.commit()
    return updated


def increment_item_views(session: Session, item: Item, viewer_key: str | None = None) -> Item:
    if not viewer_key:
        item.views += 1
        session.commit()
        session.refresh(item)
        return item

    try:
        session.add(ItemView(item_id=item.id, viewer_key=viewer_key))
        item.views += 1
        session.commit()
    except IntegrityError:
        session.rollback()
        session.refresh(item)
        return item

    session.refresh(item)
    return item


def toggle_favorite(session: Session, user_id: int, item_id: int) -> tuple[bool, int]:
    favorite = session.scalar(select(Favorite).where(Favorite.user_id == user_id, Favorite.item_id == item_id))
    if favorite:
        session.delete(favorite)
        session.commit()
        favorited = False
    else:
        session.add(Favorite(user_id=user_id, item_id=item_id))
        session.commit()
        favorited = True
    favorite_count = int(session.scalar(select(func.count(Favorite.id)).where(Favorite.item_id == item_id)) or 0)
    return favorited, favorite_count


def list_favorites(
    session: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    q: str | None = None,
    category_id: int | None = None,
    sort: str = "newest",
) -> dict[str, Any]:
    stmt = (
        select(Item)
        .join(Favorite, Favorite.item_id == Item.id)
        .options(joinedload(Item.seller), joinedload(Item.category), selectinload(Item.images))
        .where(Favorite.user_id == user_id)
    )
    stmt = _apply_item_filters(stmt, q=q, category_id=category_id, min_price=None, max_price=None, condition=None, status=None, seller_id=None)
    stmt = _sort_item_query(stmt, sort)
    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    offset = (page - 1) * page_size
    items = list(session.scalars(stmt.offset(offset).limit(page_size)).unique().all())
    payload = [item_to_dict(item, favorite_ids={item.id for item in items}) for item in items]
    return {
        "items": payload,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": _count_pages(total, page_size),
    }


def list_my_items(
    session: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    q: str | None = None,
    status: str | None = None,
    sort: str = "newest",
) -> dict[str, Any]:
    stmt = _base_item_query(public_only=False).where(Item.seller_id == user_id)
    stmt = _apply_item_filters(
        stmt, q=q, category_id=None, min_price=None, max_price=None, condition=None, status=status, seller_id=user_id
    )
    stmt = _sort_item_query(stmt, sort)
    total = int(session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    offset = (page - 1) * page_size
    items = list(session.scalars(stmt.offset(offset).limit(page_size)).unique().all())
    payload = [item_to_dict(item, favorite_ids=set()) for item in items]
    return {
        "items": payload,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": _count_pages(total, page_size),
    }


def category_breakdown(session: Session) -> list[dict[str, Any]]:
    rows = session.execute(
        select(Category.id, Category.name, func.count(Item.id).label("count"))
        .join(Item, Item.category_id == Category.id, isouter=True)
        .group_by(Category.id)
        .order_by(func.count(Item.id).desc(), Category.sort_order.asc(), Category.name.asc())
    ).all()
    return [{"id": row.id, "name": row.name, "count": int(row.count or 0)} for row in rows]


def dashboard_stats(session: Session, *, current_user_id: int | None = None) -> dict[str, Any]:
    del current_user_id
    users = int(session.scalar(select(func.count(User.id))) or 0)
    items = int(session.scalar(select(func.count(Item.id))) or 0)
    active_items = int(session.scalar(select(func.count(Item.id)).where(Item.status == "active")) or 0)
    sold_items = int(session.scalar(select(func.count(Item.id)).where(Item.status == "sold")) or 0)
    hidden_items = int(session.scalar(select(func.count(Item.id)).where(Item.status == "hidden")) or 0)
    favorites = int(session.scalar(select(func.count(Favorite.id))) or 0)
    views = int(session.scalar(select(func.coalesce(func.sum(Item.views), 0))) or 0)
    categories = int(session.scalar(select(func.count(Category.id)).where(Category.is_active.is_(True))) or 0)
    orders = int(session.scalar(select(func.count(PurchaseOrder.id))) or 0)
    conversations = int(session.scalar(select(func.count(Conversation.id))) or 0)
    messages = int(session.scalar(select(func.count(ChatMessage.id))) or 0)
    notifications = int(session.scalar(select(func.count(Notification.id))) or 0)
    unread_notifications = int(
        session.scalar(select(func.count(Notification.id)).where(Notification.is_read.is_(False))) or 0
    )
    active_rate = round((active_items / items) * 100, 1) if items else 0.0
    top_items = list(
        session.scalars(
            _sort_item_query(
                _base_item_query(public_only=True).where(Item.status == "active"),
                "hot",
            ).limit(6)
        ).unique().all()
    )
    top_payload = [item_to_dict(item, favorite_ids=set()) for item in top_items]
    return {
        "users": users,
        "items": items,
        "active_items": active_items,
        "sold_items": sold_items,
        "hidden_items": hidden_items,
        "favorites": favorites,
        "views": views,
        "categories": categories,
        "orders": orders,
        "conversations": conversations,
        "messages": messages,
        "notifications": notifications,
        "unread_notifications": unread_notifications,
        "active_rate": active_rate,
        "top_items": top_payload,
        "category_breakdown": category_breakdown(session),
    }


def price_stats(session: Session) -> dict[str, Any]:
    """价格趋势统计：分类均价、价格区间分布、近7天发布趋势"""
    from datetime import datetime as dt, timedelta

    # 各分类均价
    cat_rows = session.execute(
        select(
            Category.name,
            func.count(Item.id).label("count"),
            func.avg(Item.price).label("avg_price"),
            func.min(Item.price).label("min_price"),
            func.max(Item.price).label("max_price"),
        )
        .join(Item, Item.category_id == Category.id)
        .where(Item.status == "active")
        .group_by(Category.id)
        .order_by(Category.sort_order.asc())
    ).all()
    category_avg = [
        {
            "name": row.name,
            "count": int(row.count),
            "avg_price": round(float(row.avg_price), 2) if row.avg_price else 0,
            "min_price": round(float(row.min_price), 2) if row.min_price else 0,
            "max_price": round(float(row.max_price), 2) if row.max_price else 0,
        }
        for row in cat_rows
    ]

    # 价格区间分布
    brackets = [
        ("0-50", 0, 50),
        ("50-100", 50, 100),
        ("100-200", 100, 200),
        ("200-500", 200, 500),
        ("500-1000", 500, 1000),
        ("1000+", 1000, None),
    ]
    price_distribution = []
    active_stmt = select(Item.id).where(Item.status == "active")
    total_active = int(session.scalar(select(func.count()).select_from(active_stmt.subquery())) or 0)
    for label, lo, hi in brackets:
        stmt = select(func.count(Item.id)).where(Item.status == "active", Item.price >= lo)
        if hi is not None:
            stmt = stmt.where(Item.price < hi)
        count = int(session.scalar(stmt) or 0)
        price_distribution.append({
            "range": label,
            "count": count,
            "percent": round(count / total_active * 100, 1) if total_active else 0,
        })

    # 近 7 天发布趋势
    now = dt.utcnow()
    daily = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        next_day = day + timedelta(days=1)
        count = int(
            session.scalar(
                select(func.count(Item.id)).where(
                    Item.created_at >= day,
                    Item.created_at < next_day,
                )
            ) or 0
        )
        daily.append({"date": day.isoformat(), "count": count})

    return {
        "category_avg": category_avg,
        "price_distribution": price_distribution,
        "daily_trend": daily,
    }
