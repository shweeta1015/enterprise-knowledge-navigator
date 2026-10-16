# Production Dockerfile for Enterprise Knowledge Navigator
FROM python:3.11-slim AS runner

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py .
COPY .env.example .

# Create persistent storage directories
RUN mkdir -p data/raw data/processed data/vector_store data/graph_store data/backups logs

# Set production environment defaults
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    DEBUG=false \
    BACKEND_HOST=0.0.0.0 \
    PORT=8000

# Expose primary port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health || exit 1

# Production startup command
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
