from services.server_service import startup_checks
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import threading
from core.database import engine, Base
from controllers.page_routes import router as page_router
from controllers.proofs_routes import router as proofs_router
from controllers.test_routes import router as test_router
from controllers.socket_routes import router as socket_router
from controllers.sync_routes import router as sync_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    startup_checks(engine)
 
    yield

app = FastAPI(title="Flash Test Detection And Reporting Application",lifespan=lifespan)

# Create database tables

app.mount("/static", StaticFiles(directory="views/static"), name="static")

app.include_router(page_router)
app.include_router(proofs_router)
app.include_router(test_router)
app.include_router(socket_router)
app.include_router(sync_router)
