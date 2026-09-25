# syntax=docker/dockerfile:1.6

FROM python:3.11-slim

# Set a working directory inside the container.
WORKDIR /app

# System deps needed by psycopg and any wheels that need compilation.
# Kept minimal — we use psycopg[binary] so no Postgres client libs required.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (separate layer so rebuilds are fast
# when only source code changes).
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --timeout 120 --retries 5 -r requirements.txt

# Copy the application source.
COPY . .

# Expose the port uvicorn listens on.
EXPOSE 8000

# Healthcheck uses the app's own /health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Default command. Overridden in docker-compose for dev.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
