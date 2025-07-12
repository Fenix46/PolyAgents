#!/bin/bash

# PolyAgents Monitoring Script
# This script monitors the health of all PolyAgents services

set -e

echo "🔍 PolyAgents Service Monitor"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local service_name=$1
    local url=$2
    local description=$3
    
    echo -n "Checking $description... "
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Function to check Docker container status
check_container() {
    local container_name=$1
    local description=$2
    
    echo -n "Checking $description... "
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Not Running${NC}"
        return 1
    fi
}

# Function to check port availability
check_port() {
    local port=$1
    local description=$2
    
    echo -n "Checking $description (port $port)... "
    
    if netstat -an 2>/dev/null | grep -q ":$port.*LISTEN" || lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Available${NC}"
        return 0
    else
        echo -e "${RED}❌ Not Available${NC}"
        return 1
    fi
}

echo ""
echo "🐳 Docker Container Status:"
echo "---------------------------"

# Check Docker containers
check_container "polyagents-frontend" "Frontend Container"
check_container "polyagents-api" "API Container"
check_container "polyagents-redis" "Redis Container"
check_container "polyagents-postgres" "PostgreSQL Container"
check_container "polyagents-qdrant" "Qdrant Container"

echo ""
echo "🌐 Service Health Checks:"
echo "-------------------------"

# Check service endpoints
check_service "Frontend" "http://localhost:3000" "Frontend Web Interface"
check_service "API Health" "http://localhost:3000/health" "API Health Endpoint"
check_service "API Detailed Health" "http://localhost:3000/api/health/detailed" "API Detailed Health"

echo ""
echo "🔌 Port Availability:"
echo "--------------------"

# Check ports
check_port 3000 "Frontend"
check_port 8000 "API"
check_port 6379 "Redis"
check_port 5432 "PostgreSQL"
check_port 6333 "Qdrant"

echo ""
echo "📊 System Information:"
echo "---------------------"

# Get system stats
echo -e "${BLUE}Docker Compose Status:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}Recent Logs (last 10 lines):${NC}"
docker-compose logs --tail=10

echo ""
echo -e "${BLUE}Resource Usage:${NC}"
echo "Memory usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "🔧 Troubleshooting Commands:"
echo "----------------------------"
echo "View all logs: docker-compose logs -f"
echo "Restart services: docker-compose restart"
echo "Rebuild services: docker-compose up -d --build"
echo "Stop all services: docker-compose down"
echo "Check specific service: docker-compose logs [service-name]" 