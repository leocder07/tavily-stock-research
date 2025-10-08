#!/bin/bash

# AWS Elastic Beanstalk Deployment Script
# Stock Research System - Production Deployment

set -e  # Exit on error

echo "================================================"
echo "Stock Research System - AWS Deployment"
echo "================================================"

# Configuration
APP_NAME="stock-research-system"
ENV_NAME_PROD="stock-research-prod"
ENV_NAME_STAGING="stock-research-staging"
REGION="us-east-1"
PLATFORM="Python 3.11 running on 64bit Amazon Linux 2023"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        exit 1
    fi

    # Check EB CLI
    if ! command -v eb &> /dev/null; then
        print_error "EB CLI not found. Please install it: pip install awsebcli"
        exit 1
    fi

    # Check environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY not set. Will need to be configured in AWS."
    fi

    if [ -z "$TAVILY_API_KEY" ]; then
        print_warning "TAVILY_API_KEY not set. Will need to be configured in AWS."
    fi

    if [ -z "$MONGODB_URI" ]; then
        print_warning "MONGODB_URI not set. Will need to be configured in AWS."
    fi

    print_status "Prerequisites check complete."
}

# Initialize Elastic Beanstalk application
init_eb() {
    print_status "Initializing Elastic Beanstalk application..."

    if [ ! -d ".elasticbeanstalk" ]; then
        eb init -p "$PLATFORM" -r "$REGION" "$APP_NAME"
    else
        print_status "Elastic Beanstalk already initialized."
    fi
}

# Create deployment package
create_package() {
    print_status "Creating deployment package..."

    # Clean up previous builds
    rm -f deploy.zip

    # Create deployment package excluding unnecessary files
    zip -r deploy.zip . \
        -x "*.git*" \
        -x "*__pycache__*" \
        -x "*.pytest_cache*" \
        -x "*.env*" \
        -x "*.DS_Store" \
        -x "*node_modules*" \
        -x "*venv*" \
        -x "*env*" \
        -x "*.coverage*" \
        -x "*.mypy_cache*" \
        -x "tests/*" \
        -x "docs/*" \
        -x "deploy.sh" \
        -x "*.log"

    print_status "Deployment package created: deploy.zip"
}

# Deploy to staging
deploy_staging() {
    print_status "Deploying to STAGING environment..."

    # Create or update staging environment
    if eb status "$ENV_NAME_STAGING" 2>/dev/null; then
        print_status "Updating existing staging environment..."
        eb deploy "$ENV_NAME_STAGING" --timeout 30
    else
        print_status "Creating new staging environment..."
        eb create "$ENV_NAME_STAGING" \
            --platform "$PLATFORM" \
            --instance-type t3.medium \
            --region "$REGION" \
            --envvars \
            ENVIRONMENT=staging,\
            DEBUG=true
    fi

    # Wait for environment to be ready
    eb health "$ENV_NAME_STAGING" --refresh

    print_status "Staging deployment complete!"
    eb open "$ENV_NAME_STAGING"
}

# Deploy to production
deploy_production() {
    print_warning "Deploying to PRODUCTION environment..."

    # Confirm production deployment
    read -p "Are you sure you want to deploy to production? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_status "Production deployment cancelled."
        exit 0
    fi

    # Create or update production environment
    if eb status "$ENV_NAME_PROD" 2>/dev/null; then
        print_status "Updating existing production environment..."
        eb deploy "$ENV_NAME_PROD" --timeout 30
    else
        print_status "Creating new production environment..."
        eb create "$ENV_NAME_PROD" \
            --platform "$PLATFORM" \
            --instance-type t3.large \
            --region "$REGION" \
            --scale 2 \
            --envvars \
            ENVIRONMENT=production,\
            DEBUG=false
    fi

    # Wait for environment to be ready
    eb health "$ENV_NAME_PROD" --refresh

    print_status "Production deployment complete!"
    eb open "$ENV_NAME_PROD"
}

# Set environment variables
set_env_vars() {
    local env_name=$1
    print_status "Setting environment variables for $env_name..."

    eb setenv \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        TAVILY_API_KEY="$TAVILY_API_KEY" \
        MONGODB_URI="$MONGODB_URI" \
        REDIS_HOST="$REDIS_HOST" \
        SECRET_KEY="$SECRET_KEY" \
        JWT_SECRET_KEY="$JWT_SECRET_KEY" \
        SENTRY_DSN="$SENTRY_DSN" \
        --environment "$env_name"

    print_status "Environment variables set."
}

# Run tests before deployment
run_tests() {
    print_status "Running tests..."

    # Run Python tests
    python -m pytest tests/ -v --cov=. --cov-report=term-missing || {
        print_error "Tests failed. Aborting deployment."
        exit 1
    }

    print_status "All tests passed!"
}

# Monitor deployment
monitor_deployment() {
    local env_name=$1
    print_status "Monitoring deployment for $env_name..."

    # Stream logs
    eb logs "$env_name" --stream
}

# Main deployment flow
main() {
    echo "Select deployment target:"
    echo "1) Staging"
    echo "2) Production"
    echo "3) Both (Staging first, then Production)"
    read -p "Enter choice (1-3): " choice

    check_prerequisites
    init_eb
    run_tests
    create_package

    case $choice in
        1)
            deploy_staging
            set_env_vars "$ENV_NAME_STAGING"
            ;;
        2)
            deploy_production
            set_env_vars "$ENV_NAME_PROD"
            ;;
        3)
            deploy_staging
            set_env_vars "$ENV_NAME_STAGING"

            print_status "Staging deployed. Test the staging environment before proceeding."
            read -p "Continue with production deployment? (yes/no): " continue_prod

            if [ "$continue_prod" == "yes" ]; then
                deploy_production
                set_env_vars "$ENV_NAME_PROD"
            fi
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    print_status "Deployment complete!"
    print_status "Use 'eb ssh' to connect to instances"
    print_status "Use 'eb logs' to view logs"
    print_status "Use 'eb health' to check health status"
}

# Run main function
main