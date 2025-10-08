#!/bin/bash

# System Verification Script for Stock Research System
# Run this before demo or deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "================================================"
echo "   Stock Research System - Verification Tool   "
echo "================================================"
echo ""

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Initialize counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to perform check
check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if eval "$2" &> /dev/null; then
        print_success "$1"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        print_error "$1"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# 1. Check Python installation
echo "🐍 Python Environment"
echo "--------------------"
check "Python 3.11+ installed" "python3 --version | grep -E '3\.(1[1-9]|[2-9][0-9])'"
check "pip installed" "pip3 --version"
echo ""

# 2. Check Node.js installation
echo "📦 Node.js Environment"
echo "----------------------"
check "Node.js installed" "node --version"
check "npm installed" "npm --version"
echo ""

# 3. Check Backend Dependencies
echo "🔧 Backend Dependencies"
echo "-----------------------"
cd backend 2>/dev/null || cd stock-research-system/backend
check "requirements.txt exists" "test -f requirements.txt"
check "FastAPI installed" "python3 -c 'import fastapi'"
check "LangGraph installed" "python3 -c 'import langgraph'"
check "Tavily installed" "python3 -c 'import tavily'"
check "MongoDB Motor installed" "python3 -c 'import motor'"
cd - > /dev/null
echo ""

# 4. Check Frontend Dependencies
echo "🎨 Frontend Dependencies"
echo "------------------------"
cd frontend 2>/dev/null || cd stock-research-system/frontend
check "package.json exists" "test -f package.json"
check "node_modules exists" "test -d node_modules"
check "React installed" "test -d node_modules/react"
check "Clerk installed" "test -d node_modules/@clerk/clerk-react"
cd - > /dev/null
echo ""

# 5. Check Environment Variables
echo "🔐 Environment Configuration"
echo "----------------------------"
cd backend 2>/dev/null || cd stock-research-system/backend
check ".env file exists" "test -f .env"

if [ -f .env ]; then
    check "TAVILY_API_KEY set" "grep -q '^TAVILY_API_KEY=' .env"
    check "OPENAI_API_KEY set" "grep -q '^OPENAI_API_KEY=' .env"
    check "MONGODB_URL set" "grep -q '^MONGODB_URL=' .env"
fi

cd ../frontend 2>/dev/null
check "Frontend .env.local exists" "test -f .env.local"

if [ -f .env.local ]; then
    check "VITE_CLERK_PUBLISHABLE_KEY set" "grep -q '^VITE_CLERK_PUBLISHABLE_KEY=' .env.local"
fi
cd - > /dev/null
echo ""

# 6. Check Services
echo "🚀 Service Status"
echo "-----------------"

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "Backend API is running on port 8000"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))

    # Check health status
    HEALTH_STATUS=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin)['mongodb']['status'])" 2>/dev/null || echo "unknown")
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        print_success "MongoDB connection is healthy"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        print_error "MongoDB connection issue: $HEALTH_STATUS"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
else
    print_warning "Backend API is not running"
    print_info "Start with: cd backend && python3 -m uvicorn main:app --reload --port 8000"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    print_success "Frontend is running on port 3000"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    print_warning "Frontend is not running"
    print_info "Start with: cd frontend && npm start"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# 7. Check Project Structure
echo "📁 Project Structure"
echo "--------------------"
check "Backend agents directory exists" "test -d backend/agents"
check "Frontend components directory exists" "test -d frontend/src/components"
check "Documentation exists" "test -f ARCHITECTURE.md"
check "Demo script exists" "test -f DEMO_SCRIPT.md"
echo ""

# 8. Check API Endpoints
if curl -s http://localhost:8000/health > /dev/null; then
    echo "🔌 API Endpoints"
    echo "----------------"
    check "Health endpoint accessible" "curl -s http://localhost:8000/health"
    check "API docs accessible" "curl -s http://localhost:8000/docs"
    check "User profile endpoint exists" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/user/profile/test | grep -E '404|422'"
    echo ""
fi

# 9. Summary
echo "================================================"
echo "                   SUMMARY                      "
echo "================================================"
echo ""

TOTAL_CHECKS=$((PASSED_CHECKS + FAILED_CHECKS))

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! ($PASSED_CHECKS/$TOTAL_CHECKS)${NC}"
    echo "System is ready for demo or deployment!"
else
    echo -e "${YELLOW}⚠️  Some checks failed ($FAILED_CHECKS/$TOTAL_CHECKS)${NC}"
    echo ""
    echo "Passed: $PASSED_CHECKS"
    echo "Failed: $FAILED_CHECKS"
    echo ""
    echo "Please address the failed checks before proceeding."
fi

echo ""
echo "================================================"
echo ""

# 10. Quick Start Guide
if [ $FAILED_CHECKS -gt 0 ]; then
    echo "📋 Quick Setup Commands:"
    echo "------------------------"
    echo ""
    echo "1. Install Backend Dependencies:"
    echo "   cd backend && pip3 install -r requirements.txt"
    echo ""
    echo "2. Install Frontend Dependencies:"
    echo "   cd frontend && npm install --legacy-peer-deps"
    echo ""
    echo "3. Set up environment variables:"
    echo "   Copy .env.example to .env and fill in values"
    echo ""
    echo "4. Start Backend:"
    echo "   cd backend && python3 -m uvicorn main:app --reload --port 8000"
    echo ""
    echo "5. Start Frontend:"
    echo "   cd frontend && npm start"
    echo ""
fi

exit $FAILED_CHECKS