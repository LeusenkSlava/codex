from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.inbound.http.router import make_fastapi_root_router
from src.main.config.logging import setup_logging
from src.main.config.settings import settings
from src.main.setup.admin import setup_admin
from src.outbound.database.session import engine

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_admin(app, engine)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.app.SERVICE_NAME,
    version="1.0.0",
    summary=f"OpenAPI schema for {settings.app.SERVICE_NAME}",
    root_path=settings.app.ROOT_PATH.rstrip("/"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(make_fastapi_root_router(debug_mode=settings.app.DEBUG_MODE))
