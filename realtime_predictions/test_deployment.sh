#!/bin/bash

# Test Deployment Script
# Run this before deploying to Render.com to catch issues early

set -e  # Exit on error

echo "🧪 Testing Realtime Predictions Deployment..."
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "\n${YELLOW}1. Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check required files
echo -e "\n${YELLOW}2. Checking required files...${NC}"
files=(
    "Dockerfile"
    ".dockerignore"
    "requirements.txt"
    "start_server.py"
    "api_server.py"
    "render.yaml"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done

# Optional files check
echo -e "\n${YELLOW}3. Checking optional files (warnings only)...${NC}"
optional_files=(
    "models/realtime_behavior_model.pkl"
    "data/firestore_data.csv"
)

for file in "${optional_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing (optional): $file${NC}"
        echo "   API will start in degraded mode without this file"
    fi
done

# Build Docker image
echo -e "\n${YELLOW}4. Building Docker image...${NC}"
if docker build -t behavior-api-test . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    echo "Run: docker build -t behavior-api-test . (without redirect) to see errors"
    exit 1
fi

# Start container in background
echo -e "\n${YELLOW}5. Starting container...${NC}"
CONTAINER_ID=$(docker run -d -p 8001:8000 -e PORT=8000 behavior-api-test)
echo -e "${GREEN}✅ Container started: ${CONTAINER_ID:0:12}${NC}"

# Wait for server to start
echo -e "\n${YELLOW}6. Waiting for server to start...${NC}"
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is healthy${NC}"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -n "."
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "\n${RED}❌ Server failed to start within ${MAX_WAIT} seconds${NC}"
    echo "Container logs:"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID > /dev/null 2>&1
    docker rm $CONTAINER_ID > /dev/null 2>&1
    exit 1
fi

# Test endpoints
echo -e "\n${YELLOW}7. Testing endpoints...${NC}"

# Health endpoint
echo -n "   /health ... "
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    FAILED=1
fi

# Status endpoint
echo -n "   /status ... "
if curl -f http://localhost:8001/status > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    FAILED=1
fi

# Root endpoint
echo -n "   / (root) ... "
if curl -f http://localhost:8001/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    FAILED=1
fi

# Docs endpoint
echo -n "   /docs ... "
if curl -f http://localhost:8001/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    FAILED=1
fi

# Cleanup
echo -e "\n${YELLOW}8. Cleaning up...${NC}"
docker stop $CONTAINER_ID > /dev/null 2>&1
docker rm $CONTAINER_ID > /dev/null 2>&1
echo -e "${GREEN}✅ Container stopped and removed${NC}"

# Final result
echo -e "\n================================================"
if [ -z "$FAILED" ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}Your deployment is ready for Render.com${NC}"
    echo -e "\nNext steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'Add realtime predictions service'"
    echo "  3. git push"
    echo "  4. Deploy on Render.com"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "Please fix the issues before deploying"
    exit 1
fi

