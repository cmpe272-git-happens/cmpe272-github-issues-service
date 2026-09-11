from fastapi import FastAPI

from app.routes.events import router as events_router
from app.routes.health import router as health_router
from app.routes.issues import router as issues_router
from app.routes.webhook import router as webhook_router

app = FastAPI(
    title="GitHub Issues Service",
    description="A service wrapper around the GitHub Issues REST API",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(issues_router)
app.include_router(webhook_router)
app.include_router(events_router)
