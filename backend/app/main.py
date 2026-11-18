import os
import uuid
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.database import init_db, SessionLocal, get_db
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.services.audit_logger import AuditLogger
from backend.app.exceptions import NexusOpsBaseException
from backend.app.api.incidents import router as incidents_router
from backend.app.api.actions import router as actions_router
from backend.app.api.simulator import router as simulator_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.websocket import router as websocket_router

logger = logging.getLogger("nexusops.security")

# ========================================================
# Security Middleware: Enterprise HTTP Response Headers
# ========================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Enforce payload size bounds
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "PAYLOAD_TOO_LARGE",
                    "message": f"Request body exceeds maximum authorized size of {settings.max_request_body_bytes} bytes."
                }
            )

        response = await call_next(request)

        # 2. Hardened Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response

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

# Register Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Enable Strict Configurable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global Exception Handlers (Prevent stack trace leakage)
@app.exception_handler(NexusOpsBaseException)
async def handle_nexusops_domain_exception(request: Request, exc: NexusOpsBaseException):
    err_id = f"err-{uuid.uuid4().hex[:8]}"
    logger.warning(f"[{err_id}] Domain exception: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
            "error_id": err_id
        }
    )

@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception):
    err_id = f"err-{uuid.uuid4().hex[:8]}"
    logger.error(f"[{err_id}] Unhandled server exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected operational error occurred. The incident has been recorded.",
            "error_id": err_id
        }
    )

# Register API routers
app.include_router(incidents_router)
app.include_router(actions_router)
app.include_router(simulator_router)
app.include_router(metrics_router)
app.include_router(websocket_router)

# Health & Security Check
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Verify cryptographic audit chain status
    chain_valid, tamper_msg, count = AuditLogger.verify_chain_integrity(db)
    return {
        "status": "healthy",
        "service": "NexusOps Enterprise Operations Engine",
        "mock_mode": settings.mock_mode,
        "chaos_mode": settings.chaos_mode,
        "model": settings.gemini_model,
        "audit_chain": {
            "valid": chain_valid,
            "records_verified": count,
            "status": "TAMPER_FREE" if chain_valid else "CORRUPTED"
        }
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
