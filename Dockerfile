# =======================================================
# Stage 1: Build React Frontend
# =======================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# =======================================================
# Stage 2: Production Python Backend & Cloud Run Runtime
# =======================================================
FROM python:3.11-slim AS production

# System dependencies & non-root user
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code, simulator, docs, and environment configuration
COPY backend/ /app/backend/
COPY simulator/ /app/simulator/
COPY .env.example /app/.env.example

# Copy built frontend assets from stage 1 into frontend/dist
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Expose Google Cloud Run port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Google Cloud Run dynamically injects $PORT (default 8080)
CMD exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}
