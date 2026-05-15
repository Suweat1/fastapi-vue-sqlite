from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .crud import ensure_default_categories
from .database import SessionLocal, create_all_tables
from .realtime import realtime_manager
from .routers import admin, auth, categories, chats, favorites, notifications, items, orders, stats, upload, ws


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(categories.router, prefix=settings.api_prefix)
app.include_router(items.router, prefix=settings.api_prefix)
app.include_router(orders.router, prefix=settings.api_prefix)
app.include_router(chats.router, prefix=settings.api_prefix)
app.include_router(notifications.router, prefix=settings.api_prefix)
app.include_router(favorites.router, prefix=settings.api_prefix)
app.include_router(upload.router, prefix=settings.api_prefix)
app.include_router(stats.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(ws.router, prefix=settings.api_prefix)


@app.on_event("startup")
async def on_startup():
    realtime_manager.set_loop(asyncio.get_running_loop())
    create_all_tables()
    db = SessionLocal()
    try:
        ensure_default_categories(db)
    finally:
        db.close()


@app.on_event("shutdown")
async def on_shutdown():
    await realtime_manager.shutdown()


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": settings.app_name}
