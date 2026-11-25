# Multi-stage Dockerfile for agent dong (Phase 20.1 - G13)

# ── Stage 1: Builder ──
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/install/bin:${PATH}" \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser

# Copy installed Python packages & binaries from builder
COPY --from=builder /install /usr/local

# Copy application code, resource files, and configuration into container image
COPY src/ ./src/
COPY resource/ ./resource/
COPY config/ ./config/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# HEALTHCHECK calls /ready (fallback to /api/health for basic liveness check if needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ready || curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
