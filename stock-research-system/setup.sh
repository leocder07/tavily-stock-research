#!/bin/bash

echo "=================================="
echo "Stock Research System Setup Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
echo "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js
echo "Checking Node.js installation..."
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"
else
    echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo ""
echo "Setting up Backend..."
echo "--------------------"

# Navigate to backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}!${NC} Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}!${NC} Please edit backend/.env with your API keys:"
    echo "   - TAVILY_API_KEY"
    echo "   - OPENAI_API_KEY"
    echo "   - MONGODB_URL"
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

echo ""
echo "Setting up Frontend..."
echo "---------------------"

# Navigate to frontend
cd ../frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install --silent

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}!${NC} Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓${NC} Frontend .env created with default settings"
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

echo ""
echo "=================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your API keys"
echo "2. Start the backend:"
echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend && npm start"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "For Docker deployment, run:"
echo "   docker-compose up --build"
echo ""