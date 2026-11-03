#!/bin/bash
# Startup script for Trade Assessment API

set -e

echo "=================================================="
echo "Trade Assessment API - Startup"
echo "=================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating from template..."
    cp api/.env.example .env
    echo "✅ .env created - Please update with your configuration"
    echo "   Especially: AUTHORIZED_API_KEYS"
    exit 1
fi

# Generate API keys if needed
if ! grep -q "key1,key2,key3" .env; then
    echo "✅ Using existing .env configuration"
else
    echo "⚠️  Using default API keys - Consider generating new ones:"
    echo "   python api/generate_keys.py --count 1"
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Install Docker from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Build and start container
echo ""
echo "Building Docker image..."
docker-compose -f api/docker-compose.yml build

echo ""
echo "Starting Trade Assessment API..."
docker-compose -f api/docker-compose.yml up -d

sleep 2

# Check if API is running
if docker ps | grep -q trade-assessment-api; then
    echo ""
    echo "✅ API is running!"
    echo ""
    echo "Access the API at: http://localhost:8000"
    echo "Interactive docs: http://localhost:8000/docs"
    echo "Alternative docs: http://localhost:8000/redoc"
    echo ""
    echo "View logs: docker-compose -f api/docker-compose.yml logs -f"
    echo "Stop API: docker-compose -f api/docker-compose.yml down"
else
    echo "❌ Failed to start API"
    docker-compose -f api/docker-compose.yml logs
    exit 1
fi
