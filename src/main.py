import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from contextlib import asynccontextmanager
from src.routers import routers
from src.config import settings
import redis.asyncio as aioredis
from src.database import engine, redis_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event manager for startup and shutdown."""
    logger.info("Application is starting...")

    redis = aioredis.Redis(connection_pool=redis_pool)
    await FastAPILimiter.init(redis)

    yield  # Everything before `yield` runs at startup, everything after runs at shutdown.

    logger.info("Application is shutting down...")


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

allowed_origins = settings.ALLOWED_ORIGINS.split(",")

@app.get("/ping")
async def read_root(request: Request):
    origin = request.headers.get("origin")
    return {
        "message": "pong",
        "origin": request.headers.get("origin"),
        "host": request.headers.get("host"),
        "referer": request.headers.get("referer"),
        "user-agent": request.headers.get("user-agent"),
        "x-forwarded-for": request.headers.get("x-forwarded-for"),
        "all_headers": dict(request.headers),
        "client": {"host": request.client.host, "port": request.client.port},
        "allowed_origins": allowed_origins,
    }

for router in routers:
    app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)