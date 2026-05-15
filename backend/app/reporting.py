from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from . import crud
from .models import Category, Item, User


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _csv_bytes(fieldnames: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _format_cell(row.get(field)) for field in fieldnames})
    return buffer.getvalue().encode("utf-8-sig")


def _flatten_item(item: Item) -> dict[str, Any]:
    images = list(item.images or [])
    return {
        "id": item.id,
        "title": item.title,
        "price": item.price,
        "status": item.status,
        "views": item.views,
        "is_featured": item.is_featured,
        "condition": item.condition,
        "location": item.location,
        "seller": item.seller.nickname or item.seller.username,
        "seller_username": item.seller.username,
        "category": item.category.name,
        "image_count": len(images),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _flatten_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


def build_dashboard_export(session: Session) -> tuple[bytes, str]:
    stats = crud.dashboard_stats(session)
    users = list(session.scalars(select(User).order_by(desc(User.created_at), desc(User.id))).all())
    items = list(
        session.scalars(
            crud._base_item_query(public_only=False).order_by(desc(Item.created_at), desc(Item.id))
        )
        .unique()
        .all()
    )
    categories = list(session.scalars(select(Category).order_by(Category.sort_order.asc(), Category.name.asc())).all())

    summary_rows = [
        {"指标": "用户数", "数值": stats["users"]},
        {"指标": "商品数", "数值": stats["items"]},
        {"指标": "上架商品", "数值": stats["active_items"]},
        {"指标": "已售出商品", "数值": stats["sold_items"]},
        {"指标": "隐藏商品", "数值": stats["hidden_items"]},
        {"指标": "收藏数", "数值": stats["favorites"]},
        {"指标": "累计浏览", "数值": stats["views"]},
        {"指标": "分类数", "数值": stats["categories"]},
        {"指标": "订单数", "数值": stats["orders"]},
        {"指标": "会话数", "数值": stats["conversations"]},
        {"指标": "消息数", "数值": stats["messages"]},
        {"指标": "通知数", "数值": stats["notifications"]},
        {"指标": "未读通知", "数值": stats["unread_notifications"]},
        {"指标": "上架率(%)", "数值": stats["active_rate"]},
    ]

    top_items_rows = [_flatten_item(item) for item in items[:20]]
    items_rows = [_flatten_item(item) for item in items]
    user_rows = [_flatten_user(user) for user in users]
    category_rows = [
        {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "sort_order": category.sort_order,
            "is_active": category.is_active,
            "created_at": category.created_at,
        }
        for category in categories
    ]
    breakdown_rows = [
        {
            "id": row["id"],
            "name": row["name"],
            "count": row["count"],
        }
        for row in stats["category_breakdown"]
    ]

    report = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "summary": stats,
        "users": user_rows,
        "items": items_rows,
        "categories": category_rows,
        "top_items": top_items_rows,
        "category_breakdown": breakdown_rows,
    }

    summary_csv = _csv_bytes(["指标", "数值"], summary_rows)
    category_csv = _csv_bytes(["id", "name", "count"], breakdown_rows)
    top_items_csv = _csv_bytes(
        [
            "id",
            "title",
            "price",
            "status",
            "views",
            "is_featured",
            "condition",
            "location",
            "seller",
            "seller_username",
            "category",
            "image_count",
            "created_at",
            "updated_at",
        ],
        top_items_rows,
    )
    users_csv = _csv_bytes(["id", "username", "nickname", "email", "role", "is_active", "created_at"], user_rows)
    items_csv = _csv_bytes(
        [
            "id",
            "title",
            "price",
            "status",
            "views",
            "is_featured",
            "condition",
            "location",
            "seller",
            "seller_username",
            "category",
            "image_count",
            "created_at",
            "updated_at",
        ],
        items_rows,
    )
    categories_csv = _csv_bytes(["id", "name", "slug", "sort_order", "is_active", "created_at"], category_rows)
    report_json = json.dumps(report, ensure_ascii=False, default=str, indent=2).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("dashboard-summary.csv", summary_csv)
        archive.writestr("category-breakdown.csv", category_csv)
        archive.writestr("top-items.csv", top_items_csv)
        archive.writestr("users.csv", users_csv)
        archive.writestr("items.csv", items_csv)
        archive.writestr("categories.csv", categories_csv)
        archive.writestr("dashboard-report.json", report_json)
    buffer.seek(0)
    filename = f"campus-dashboard-report-{datetime.utcnow():%Y%m%d-%H%M%S}.zip"
    return buffer.getvalue(), filename
