import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file from project root or backend dir
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

def parse_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "*"
    ]

class Settings(BaseModel):
    mock_mode: bool = Field(default_factory=lambda: os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes"))
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./nexusops.db"))
    chaos_mode: bool = Field(default_factory=lambda: os.getenv("CHAOS_MODE", "false").lower() in ("true", "1", "yes"))
    cors_origins: List[str] = Field(default_factory=parse_cors_origins)
    max_request_body_bytes: int = Field(default_factory=lambda: int(os.getenv("MAX_REQUEST_BODY_BYTES", str(2 * 1024 * 1024))))
    audit_genesis_hash: str = Field(default="NEXUSOPS_GENESIS_ROOT_V1")

settings = Settings()
