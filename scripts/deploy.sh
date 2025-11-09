#!/bin/bash
# Deployment script for AI Auto-Annotation Tool

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
ACTION=${2:-up}

echo -e "${BLUE}===================================="
echo "AI Auto-Annotation Tool - Deployment"
echo -e "====================================${NC}\n"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
fi

print_success "Docker and Docker Compose are installed"

# Check environment
case $ENVIRONMENT in
    development|dev)
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env"
        print_info "Environment: Development"
        ;;
    production|prod)
        COMPOSE_FILE="docker-compose.yml -f docker-compose.prod.yml"
        ENV_FILE=".env"
        print_info "Environment: Production"
        ;;
    *)
        print_error "Unknown environment: $ENVIRONMENT. Use 'development' or 'production'"
        ;;
esac

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_warning ".env file not found. Creating from template..."

    if [ -f ".env.docker" ]; then
        cp .env.docker .env
        print_success "Created .env from .env.docker template"
        print_warning "Please edit .env file with your configuration before deploying"
        exit 0
    else
        print_error ".env.docker template not found"
    fi
fi

print_success "Environment file found: $ENV_FILE"

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p storage/images storage/datasets storage/models logs

if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "prod" ]; then
    sudo mkdir -p /var/lib/qwen3vl/{postgres,redis,storage}
    sudo mkdir -p /var/log/qwen3vl/nginx
    print_success "Created production directories"
fi

# Execute action
case $ACTION in
    up|start)
        print_info "Starting services..."
        docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d
        print_success "Services started successfully"

        # Wait for services to be healthy
        print_info "Waiting for services to be ready..."
        sleep 10

        # Check service health
        print_info "Checking service health..."
        docker-compose -f $COMPOSE_FILE ps

        # Show logs
        print_info "Recent logs:"
        docker-compose -f $COMPOSE_FILE logs --tail=20
        ;;

    down|stop)
        print_info "Stopping services..."
        docker-compose -f $COMPOSE_FILE down
        print_success "Services stopped successfully"
        ;;

    restart)
        print_info "Restarting services..."
        docker-compose -f $COMPOSE_FILE restart
        print_success "Services restarted successfully"
        ;;

    build)
        print_info "Building images..."
        docker-compose -f $COMPOSE_FILE build --no-cache
        print_success "Images built successfully"
        ;;

    rebuild)
        print_info "Rebuilding and restarting services..."
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE build --no-cache
        docker-compose -f $COMPOSE_FILE up -d
        print_success "Services rebuilt and restarted successfully"
        ;;

    logs)
        docker-compose -f $COMPOSE_FILE logs -f
        ;;

    ps|status)
        docker-compose -f $COMPOSE_FILE ps
        ;;

    clean)
        print_warning "This will remove all containers, volumes, and images"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cleaning up..."
            docker-compose -f $COMPOSE_FILE down -v --rmi all
            print_success "Cleanup completed"
        else
            print_info "Cleanup cancelled"
        fi
        ;;

    migrate)
        print_info "Running database migrations..."
        docker-compose -f $COMPOSE_FILE exec backend alembic upgrade head
        print_success "Migrations completed"
        ;;

    shell)
        SERVICE=${3:-backend}
        print_info "Opening shell in $SERVICE container..."
        docker-compose -f $COMPOSE_FILE exec $SERVICE sh
        ;;

    *)
        echo "Usage: $0 [environment] [action]"
        echo ""
        echo "Environments:"
        echo "  development, dev       Development environment"
        echo "  production, prod       Production environment"
        echo ""
        echo "Actions:"
        echo "  up, start              Start all services"
        echo "  down, stop             Stop all services"
        echo "  restart                Restart all services"
        echo "  build                  Build Docker images"
        echo "  rebuild                Rebuild and restart services"
        echo "  logs                   View service logs"
        echo "  ps, status             Show service status"
        echo "  clean                  Remove all containers and volumes"
        echo "  migrate                Run database migrations"
        echo "  shell [service]        Open shell in container"
        exit 1
        ;;
esac

echo ""
print_success "Operation completed successfully!"

# Show useful information
if [ "$ACTION" = "up" ] || [ "$ACTION" = "start" ]; then
    echo ""
    echo -e "${BLUE}Services are running at:${NC}"
    echo "  - Frontend:  http://localhost:${FRONTEND_PORT:-3000}"
    echo "  - Backend:   http://localhost:${API_PORT:-8000}"
    echo "  - API Docs:  http://localhost:${API_PORT:-8000}/docs"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop services:    docker-compose down"
    echo "  Restart services: docker-compose restart"
    echo ""
fi

exit 0
