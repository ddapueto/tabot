from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analytics,
    auth,
    broadcasts,
    catalog,
    conversations,
    dashboard,
    follow_ups,
    health,
    kb,
    leads,
    onboarding,
    settings_api,
)
from app.api.webhooks import instagram, whatsapp
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    yield
    # Shutdown
    from app.database import engine

    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="AI-powered multichannel sales assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(whatsapp.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(follow_ups.router, prefix="/api/follow-ups", tags=["follow-ups"])
app.include_router(broadcasts.router, prefix="/api/broadcasts", tags=["broadcasts"])
app.include_router(instagram.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
