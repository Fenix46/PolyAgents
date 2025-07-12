#!/bin/bash

# PolyAgents Frontend Test Setup
# This script sets up and tests the frontend integration

set -e

echo "🧪 PolyAgents Frontend Test Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if backend is running
echo -e "${BLUE}Checking backend availability...${NC}"

if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is running${NC}"
else
    echo -e "${RED}❌ Backend API is not running${NC}"
    echo "Please start the backend first:"
    echo "  docker-compose up -d api redis postgres qdrant"
    exit 1
fi

# Check if frontend dependencies are installed
echo -e "${BLUE}Checking frontend dependencies...${NC}"

if [ -d "node_modules" ]; then
    echo -e "${GREEN}✅ Dependencies are installed${NC}"
else
    echo -e "${YELLOW}⚠️  Installing dependencies...${NC}"
    npm install
fi

# Check environment configuration
echo -e "${BLUE}Checking environment configuration...${NC}"

if [ -f "env.development" ]; then
    echo -e "${GREEN}✅ Development environment file exists${NC}"
else
    echo -e "${YELLOW}⚠️  Creating development environment file...${NC}"
    cat > env.development << EOF
# Development environment configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000/ws
VITE_API_KEY=pa_dev_key_123
EOF
fi

# Test API connectivity
echo -e "${BLUE}Testing API connectivity...${NC}"

# Test basic health endpoint
if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health endpoint accessible${NC}"
else
    echo -e "${RED}❌ Health endpoint not accessible${NC}"
fi

# Test detailed health endpoint (requires API key)
if curl -f -s -H "Authorization: Bearer pa_dev_key_123" "http://localhost:8000/health/detailed" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Detailed health endpoint accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Detailed health endpoint requires valid API key${NC}"
fi

# Test WebSocket connectivity
echo -e "${BLUE}Testing WebSocket connectivity...${NC}"

# Simple WebSocket test using curl (basic check)
if curl -f -s -I "http://localhost:8000/ws/test" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WebSocket endpoint accessible${NC}"
else
    echo -e "${YELLOW}⚠️  WebSocket endpoint may require specific headers${NC}"
fi

# Build test
echo -e "${BLUE}Testing frontend build...${NC}"

if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend builds successfully${NC}"
else
    echo -e "${RED}❌ Frontend build failed${NC}"
    echo "Running build with verbose output:"
    npm run build
fi

echo ""
echo -e "${GREEN}🎉 Frontend test setup completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Start the development server: npm run dev"
echo "2. Open http://localhost:8080 in your browser"
echo "3. Test the chat interface with the backend"
echo ""
echo "Development commands:"
echo "  npm run dev          - Start development server"
echo "  npm run build        - Build for production"
echo "  npm run preview      - Preview production build"
echo "  npm run lint         - Run ESLint"
echo ""
echo "Docker development:"
echo "  docker-compose -f ../docker-compose.dev.yml up -d"
echo "  # Access at http://localhost:8080" 