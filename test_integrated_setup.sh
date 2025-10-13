#!/bin/bash

# Test Integrated Setup
# Quick validation that both services can run together

set -e

echo "🧪 Testing Integrated Setup..."
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
echo -e "\n${YELLOW}1. Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $PYTHON_CMD${NC}"

# Check required files
echo -e "\n${YELLOW}2. Checking files...${NC}"
files=(
    "server.py"
    "start_all_services.py"
    "requirements.txt"
    "realtime_predictions/api_server.py"
    "realtime_predictions/start_server.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done

# Check if dependencies are installed
echo -e "\n${YELLOW}3. Checking dependencies...${NC}"
echo "   (This may take a moment...)"

if $PYTHON_CMD -c "import fastapi, uvicorn, pandas, sklearn" 2>/dev/null; then
    echo -e "${GREEN}✅ All prediction API dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some dependencies missing${NC}"
    echo "   Run: pip install -r requirements.txt"
    echo "   Continuing anyway..."
fi

# Test import of realtime_predictions module
echo -e "\n${YELLOW}4. Testing module imports...${NC}"
if $PYTHON_CMD -c "import sys; sys.path.insert(0, 'realtime_predictions'); from services.predictor import RealtimeBehaviorPredictor" 2>/dev/null; then
    echo -e "${GREEN}✅ Realtime predictions module imports successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Module import warning (may need dependencies)${NC}"
fi

# Check port availability
echo -e "\n${YELLOW}5. Checking port availability...${NC}"
PORT=5000
API_PORT=5001

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is in use${NC}"
else
    echo -e "${GREEN}✅ Port $PORT available${NC}"
fi

if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $API_PORT is in use${NC}"
else
    echo -e "${GREEN}✅ Port $API_PORT available${NC}"
fi

# Final summary
echo -e "\n========================================"
echo -e "${GREEN}✅ Setup validation complete!${NC}"
echo ""
echo "🎯 Deployment Options:"
echo ""
echo "Option 1 - Keep Current (WebSocket only):"
echo "  python server.py"
echo ""
echo "Option 2 - Run Both Services:"
echo "  python start_all_services.py"
echo ""
echo "Option 3 - Prediction API Only:"
echo "  cd realtime_predictions && python start_server.py --skip-checks"
echo ""
echo "📚 See INTEGRATED_DEPLOYMENT.md for full guide"
echo "========================================"

