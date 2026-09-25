#!/usr/bin/env bash
set -e

echo "========================================================="
echo "   APEX AGENCY OS - Automated Deployment Script        "
echo "========================================================="

# 1. Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully."
fi

# 2. Check if .env file exists, create from template if missing
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating .env from .env.example..."
    cp .env.example .env
    echo "👉 Please update your .env file with your GEMINI_API_KEY and JWT_SECRET before running in production."
fi

# 3. Build and launch containers
echo "🚀 Building and starting containers with Docker Compose..."
docker compose down || true
docker compose build --no-cache
docker compose up -d

echo "========================================================="
echo "✅ System deployed successfully!"
echo "🌐 Frontend Dashboard: http://localhost (Port 80)"
echo "⚙️  Backend API Docs:   http://localhost:8000/docs"
echo "========================================================="
