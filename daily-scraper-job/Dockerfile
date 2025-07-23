# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    PYTHONIOENCODING=utf-8

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data, logs, and state
RUN mkdir -p /app/data /app/logs /app/state

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash scraper && \
    chown -R scraper:scraper /app

# Switch to non-root user
USER scraper

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python simple_health_check.py || exit 1

# Default command - production ready
CMD ["python", "main.py", "--log-level", "INFO"]

# Labels for metadata
LABEL maintainer="OptiBot Team" \
      description="Daily scraper job for OptiSigns support articles" \
      version="1.0.0"
