# ============================
# Stage 1: Builder
# ============================
FROM python:3.10-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        build-essential \
        libssl-dev \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Create venv and install dependencies
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# ============================
# Stage 2: Final Runtime
# ============================
FROM python:3.10-slim AS final

ENV DEBIAN_FRONTEND=noninteractive

# Runtime dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system app && \
    adduser --system --group --home /app app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy application code
COPY --chown=app:app . .

# Set Python path and activate venv
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; os.path.exists('llm_calls.jsonl')" || exit 1

# Run the pipeline
CMD ["python", "run_pipeline.py"]
