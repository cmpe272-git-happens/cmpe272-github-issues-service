from dotenv import load_dotenv
from app.database import init_db

from fastapi import FastAPI

from app.logging_config import configure_logging
from app.middleware import request_id_middleware
from app.routes.events import router as events_router
from app.routes.health import router as health_router
from app.routes.issues import router as issues_router
from app.routes.webhook import router as webhook_router

load_dotenv()
init_db()
configure_logging()

app = FastAPI(
    title="GitHub Issues Service",
    description="A service wrapper around the GitHub Issues REST API",
    version="1.0.0",
)

app.middleware("http")(request_id_middleware)

app.include_router(health_router)
app.include_router(issues_router)
app.include_router(webhook_router)
app.include_router(events_router)
