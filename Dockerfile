# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: libsndfile/ffmpeg for pipecat audio paths, build tools for any wheels
# that aren't pre-built for slim, curl for healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install \
      "anthropic>=0.40.0" \
      "fastapi>=0.115.0" \
      "uvicorn[standard]>=0.32.0" \
      "pydantic>=2.9.0" \
      "pydantic-settings>=2.6.0" \
      "python-dotenv>=1.0.1" \
      "httpx>=0.27.0" \
      "python-multipart" \
      "loguru>=0.7.2" \
      "aiohttp" \
      "asyncpg>=0.29" \
      "pipecat-ai[anthropic,cartesia,deepgram,daily,silero]"

# App source
COPY src/ ./src/
COPY web/ ./web/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app/src \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8080

EXPOSE 8080

# Bind to whatever Fly puts in $PORT (defaults to 8080).
CMD ["sh", "-c", "uvicorn emoha.server:app --host 0.0.0.0 --port ${SERVER_PORT:-8080}"]
