from __future__ import annotations

from decimal import Decimal
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import crud
from backend.app.database import SessionLocal, create_all_tables
from backend.app.models import Category, Favorite, Item, ItemImage, User
from backend.app.security import hash_password


def main() -> None:
    create_all_tables()
    db = SessionLocal()
    try:
        crud.ensure_default_categories(db)
        if not db.scalar(select(User.id).limit(1)):
            admin = User(
                username="admin",
                email="admin@example.com",
                nickname="管理员",
                password_hash=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            alice = User(
                username="alice",
                email="alice@example.com",
                nickname="Alice",
                password_hash=hash_password("alice123"),
                role="user",
                is_active=True,
            )
            bob = User(
                username="bob",
                email="bob@example.com",
                nickname="Bob",
                password_hash=hash_password("bob12345"),
                role="user",
                is_active=True,
            )
            db.add_all([admin, alice, bob])
            db.flush()

            categories = {category.slug: category for category in db.query(Category).all()}
            items = [
                Item(
                    title="高数教材九成新",
                    description="适合下学期复习使用，笔记完整，价格可小刀。",
                    price=Decimal("18.00"),
                    condition="九成新",
                    location="南区宿舍",
                    status="active",
                    seller_id=alice.id,
                    category_id=categories["books"].id,
                    views=35,
                    is_featured=True,
                ),
                Item(
                    title="蓝牙耳机",
                    description="续航还不错，适合上课和跑步使用。",
                    price=Decimal("65.00"),
                    condition="八成新",
                    location="北区快递点",
                    status="active",
                    seller_id=bob.id,
                    category_id=categories["digital"].id,
                    views=88,
                    is_featured=True,
                ),
                Item(
                    title="小风扇",
                    description="夏天宿舍必备，风力足，支持三档调节。",
                    price=Decimal("12.00"),
                    condition="九成新",
                    location="校内自提",
                    status="active",
                    seller_id=alice.id,
                    category_id=categories["daily"].id,
                    views=42,
                ),
            ]
            db.add_all(items)
            db.flush()
            db.add_all(
                [
                    ItemImage(item_id=items[0].id, url="/uploads/sample-book.svg", sort_order=0),
                    ItemImage(item_id=items[1].id, url="/uploads/sample-earphone.svg", sort_order=0),
                    ItemImage(item_id=items[2].id, url="/uploads/sample-fan.svg", sort_order=0),
                    Favorite(user_id=alice.id, item_id=items[1].id),
                    Favorite(user_id=bob.id, item_id=items[0].id),
                ]
            )
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
