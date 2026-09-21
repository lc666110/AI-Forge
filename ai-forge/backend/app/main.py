import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import select

from app.api.routes import router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import register_exception_handlers
from app.core.security import hash_password
from app.models import User


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log", rotation="00:00", retention="14 days", encoding="utf-8"
    )
    async with SessionLocal() as db:
        admin = await db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not admin:
            db.add(
                User(
                    email=settings.admin_email.lower(),
                    password_hash=hash_password(settings.admin_password),
                    nickname="Administrator",
                    role="admin",
                )
            )
            await db.commit()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(router)


@app.get("/health")
async def health():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
