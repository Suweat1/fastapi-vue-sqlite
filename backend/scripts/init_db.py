"""
数据库初始化脚本

用法:
    python -m scripts.init_db              # 建表 + 种子数据（幂等）
    python -m scripts.init_db --reset      # 删除所有表后重建
    python -m scripts.init_db --skip-seed  # 只建表，不插入种子数据
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select, func

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.crud import ensure_default_categories
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import Category, Favorite, Item, ItemImage, User
from backend.app.security import hash_password

# ── 种子数据 ──────────────────────────────────────────────

SEED_USERS = [
    {"username": "admin", "email": "admin@example.com", "nickname": "管理员", "password": "admin123", "role": "admin"},
    {"username": "alice", "email": "alice@example.com", "nickname": "Alice", "password": "alice123", "role": "user"},
    {"username": "bob",   "email": "bob@example.com",   "nickname": "Bob",   "password": "bob12345", "role": "user"},
]

SEED_ITEMS = [
    {
        "title": "高数教材九成新", "description": "适合下学期复习使用，笔记完整，价格可小刀。",
        "price": 18.00, "condition": "九成新", "location": "南区宿舍",
        "views": 35, "is_featured": True, "seller": "alice", "category_slug": "books",
        "image": "/uploads/sample-book.svg",
    },
    {
        "title": "蓝牙耳机", "description": "续航还不错，适合上课和跑步使用。",
        "price": 65.00, "condition": "八成新", "location": "北区快递点",
        "views": 88, "is_featured": True, "seller": "bob", "category_slug": "digital",
        "image": "/uploads/sample-earphone.svg",
    },
    {
        "title": "小风扇", "description": "夏天宿舍必备，风力足，支持三档调节。",
        "price": 12.00, "condition": "九成新", "location": "校内自提",
        "views": 42, "is_featured": False, "seller": "alice", "category_slug": "daily",
        "image": "/uploads/sample-fan.svg",
    },
]

SEED_FAVORITES = [
    {"user": "alice", "item_index": 1},
    {"user": "bob",   "item_index": 0},
]

# ── 建表 / 重置 ──────────────────────────────────────────

def create_tables() -> None:
    from backend.app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("[init_db] 表结构已创建")


def reset_tables() -> None:
    from backend.app import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[init_db] 已重置: 删除并重建所有表")

# ── 种子数据写入 ─────────────────────────────────────────

def seed_users(session) -> dict[str, User]:
    if session.scalar(select(func.count(User.id))) > 0:
        print("[init_db] 用户表非空，跳过用户种子数据")
        return {u.username: u for u in session.scalars(select(User)).all()}

    users = {}
    for data in SEED_USERS:
        user = User(
            username=data["username"],
            email=data["email"],
            nickname=data["nickname"],
            password_hash=hash_password(data["password"]),
            role=data["role"],
            is_active=True,
        )
        session.add(user)
        users[data["username"]] = user
    session.flush()
    print(f"[init_db] 已创建 {len(users)} 个种子用户: {', '.join(users)}")
    return users


def seed_items(session, users: dict[str, User], categories: dict[str, Category]) -> list[Item]:
    if session.scalar(select(func.count(Item.id))) > 0:
        print("[init_db] 物品表非空，跳过物品种子数据")
        return list(session.scalars(select(Item)).all())

    items = []
    for data in SEED_ITEMS:
        item = Item(
            title=data["title"],
            description=data["description"],
            price=Decimal(str(data["price"])),
            condition=data["condition"],
            location=data["location"],
            status="active",
            views=data["views"],
            is_featured=data["is_featured"],
            seller_id=users[data["seller"]].id,
            category_id=categories[data["category_slug"]].id,
        )
        session.add(item)
        items.append(item)
    session.flush()

    for item, data in zip(items, SEED_ITEMS):
        session.add(ItemImage(item_id=item.id, url=data["image"], sort_order=0))
    session.flush()

    print(f"[init_db] 已创建 {len(items)} 件种子物品")
    return items


def seed_favorites(session, users: dict[str, User], items: list[Item]) -> None:
    if session.scalar(select(func.count(Favorite.id))) > 0:
        print("[init_db] 收藏表非空，跳过收藏种子数据")
        return

    for data in SEED_FAVORITES:
        session.add(Favorite(user_id=users[data["user"]].id, item_id=items[data["item_index"]].id))
    session.flush()
    print(f"[init_db] 已创建 {len(SEED_FAVORITES)} 条收藏记录")


def seed_all(session) -> None:
    ensure_default_categories(session)
    users = seed_users(session)
    categories = {c.slug: c for c in session.scalars(select(Category)).all()}
    items = seed_items(session, users, categories)
    seed_favorites(session, users, items)
    session.commit()

# ── 入口 ─────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="校园二手交易平台 — 数据库初始化")
    parser.add_argument("--reset", action="store_true", help="删除所有表后重建（慎用）")
    parser.add_argument("--skip-seed", action="store_true", help="只建表，不插入种子数据")
    args = parser.parse_args()

    if args.reset:
        reset_tables()
    else:
        create_tables()

    if not args.skip_seed:
        session = SessionLocal()
        try:
            seed_all(session)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    print("[init_db] 初始化完成")


if __name__ == "__main__":
    main()
