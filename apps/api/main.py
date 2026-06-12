from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from apps.api.config import settings
from apps.api.db.session import init_db
from apps.api.routers import health, tracks


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        if settings.database_url:
            init_db(settings.database_url)
        yield


app = FastAPI(title="Lyra API", version="1.0.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(tracks.router)
