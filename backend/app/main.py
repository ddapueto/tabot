from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import health, catalog, leads, conversations
from app.api.webhooks import whatsapp


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
