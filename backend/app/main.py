import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.models.database import init_db, SessionLocal
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.api.incidents import router as incidents_router
from backend.app.api.actions import router as actions_router
from backend.app.api.simulator import router as simulator_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.websocket import router as websocket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schemas
    init_db()
    # Seed stateful simulator with deterministic enterprise records
    db = SessionLocal()
    try:
        EnterpriseSimulator.seed_initial_state(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="NexusOps - Autonomous Enterprise Operations Platform",
    description="Multi-department operational event agent pipeline with Human-in-the-Loop approval.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite dev server and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(incidents_router)
app.include_router(actions_router)
app.include_router(simulator_router)
app.include_router(metrics_router)
app.include_router(websocket_router)

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NexusOps Enterprise Operations Engine",
        "mock_mode": settings.mock_mode,
        "chaos_mode": settings.chaos_mode,
        "model": settings.gemini_model
    }

# Mount frontend static files if built
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=True)
