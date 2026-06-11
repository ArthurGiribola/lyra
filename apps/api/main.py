from fastapi import FastAPI

from apps.api.routers import health

app = FastAPI(title="Lyra API", version="1.0.0")

app.include_router(health.router)
