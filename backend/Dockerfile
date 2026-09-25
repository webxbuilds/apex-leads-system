FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for Playwright, SQLite, and compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Install Playwright Chromium headless browser & required OS libraries
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application source code
COPY backend/ ./backend/

# Create persistent storage directories
RUN mkdir -p /app/backend/app/data /app/backend/app/static/reports /app/backend/app/static/proposals

EXPOSE 8000

ENV PYTHONPATH=/app
ENV PORT=8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
