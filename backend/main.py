"""Niv AI — FastAPI entry point."""
from __future__ import annotations
import logging, os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers.analysis import router as analysis_router
from backend.routers.reports import router as reports_router
from backend.routers.health import router as health_router

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger("niv-ai")

app = FastAPI(title="Niv AI", description="Decision Intelligence for Home Buying", version="1.0.0")

frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(CORSMiddleware,
                   allow_origins=[frontend_url] if frontend_url != "*" else ["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(health_router)

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Niv AI API running", "docs": "/docs"}

logger.info("Niv AI started")
