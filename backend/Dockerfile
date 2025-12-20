# ==================================
# WEBSCRAPER PLATFORM - Backend Dockerfile
# ==================================
# Multi-stage build for production-ready Python FastAPI application

# ==================================
# Stage 1: Base
# ==================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# ==================================
# Stage 2: Dependencies
# ==================================
FROM base as dependencies

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ==================================
# Stage 3: Playwright Setup (for scraping)
# ==================================
FROM dependencies as playwright-setup

# Install Playwright runtime dependencies explicitly (Debian trixie lacks old ttf packages)
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    fonts-unifont \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browser (stored in $PLAYWRIGHT_BROWSERS_PATH so it's shared across users)
RUN mkdir -p /ms-playwright && playwright install chromium

# ==================================
# Stage 4: Development
# ==================================
FROM playwright-setup as development

# Copy application code
COPY . .
# Copy entrypoint and normalize line endings
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /ms-playwright
RUN chmod +x /app/docker-entrypoint.sh

USER appuser

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==================================
# Stage 5: Production
# ==================================
FROM playwright-setup as production

# Copy application code only (no dev dependencies)
COPY . .
# Copy entrypoint and normalize line endings
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /ms-playwright
RUN chmod +x /app/docker-entrypoint.sh

USER appuser

# Expose port
EXPOSE 8000

# Run with gunicorn for production (or uvicorn with workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
