from services.server_service import startup_checks
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
from controllers.auth_routes import router as auth_router
from controllers.sync_routes import router as sync_router
from controllers.ui_routes import router as ui_router
from controllers.proofs_routes import router as proofs_router
from controllers.user_routes import router as user_router
from services.sync_service import sync_service
import asyncio
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await startup_checks(engine)
    sync_task = asyncio.create_task(sync_service.periodic_sync_worker())
    try:
        yield
    finally:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Main Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="views/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(sync_router)
app.include_router(ui_router)
app.include_router(proofs_router)
