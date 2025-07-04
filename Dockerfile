# Multi-stage Dockerfile for CAE (Conversational Analysis Engine)

# Stage 1: Builder
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Create wheels for all dependencies
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cae && useradd -r -g cae cae

# Set working directory
WORKDIR /app

# Copy application code
COPY requirements.txt .
COPY app/ ./app/
COPY migrations/ ./migrations/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --no-deps -r requirements.txt

# Change ownership to non-root user
RUN chown -R cae:cae /app

# Switch to non-root user
USER cae

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"] 