#!/bin/bash

# PolyAgents Deployment Script
# This script builds and deploys the complete PolyAgents stack

set -e

echo "🚀 Starting PolyAgents deployment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy env.example to .env and configure your settings."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed!"
    echo "Please install Docker Compose and try again."
    exit 1
fi

echo "📦 Building and starting services..."

# Build and start all services
docker-compose up -d --build

echo "⏳ Waiting for services to be ready..."

# Wait for services to be healthy
echo "🔍 Checking service health..."

# Wait for API service
echo "   - Waiting for API service..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        echo "   ✅ API service is ready"
        break
    fi
    sleep 1
    counter=$((counter + 1))
done

if [ $counter -eq $timeout ]; then
    echo "   ❌ API service failed to start within $timeout seconds"
    echo "📋 Checking service logs..."
    docker-compose logs api
    exit 1
fi

# Wait for frontend service
echo "   - Waiting for frontend service..."
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "   ✅ Frontend service is ready"
        break
    fi
    sleep 1
    counter=$((counter + 1))
done

if [ $counter -eq $timeout ]; then
    echo "   ❌ Frontend service failed to start within $timeout seconds"
    echo "📋 Checking service logs..."
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "🎉 PolyAgents deployment completed successfully!"
echo ""
echo "📱 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:3000/api"
echo "   WebSocket: ws://localhost:3000/ws"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: docker-compose pull && docker-compose up -d"
echo ""
echo "📊 Monitor services:"
echo "   docker-compose ps"
echo "   docker-compose logs [service-name]"
echo "" 