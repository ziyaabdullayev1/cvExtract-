#!/bin/bash

# Docker management scripts for CVExtract Pro

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Development mode
dev() {
    print_status "Starting CVExtract Pro in development mode..."
    check_docker
    docker-compose up --build
}

# Production mode
prod() {
    print_status "Starting CVExtract Pro in production mode..."
    check_docker
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    print_success "Application started in production mode at http://localhost:5000"
}

# Stop containers
stop() {
    print_status "Stopping CVExtract Pro..."
    docker-compose down
    print_success "Application stopped"
}

# Clean up
clean() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup completed"
}

# View logs
logs() {
    print_status "Showing application logs..."
    docker-compose logs -f
}

# Health check
health() {
    print_status "Checking application health..."
    if curl -f http://localhost:5000/ > /dev/null 2>&1; then
        print_success "Application is healthy"
    else
        print_error "Application is not responding"
        exit 1
    fi
}

# Build only
build() {
    print_status "Building Docker image..."
    check_docker
    docker-compose build
    print_success "Docker image built successfully"
}

# Show help
help() {
    echo "CVExtract Pro Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev     Start in development mode (with hot reloading)"
    echo "  prod    Start in production mode"
    echo "  stop    Stop the application"
    echo "  clean   Stop and clean up all resources"
    echo "  logs    Show application logs"
    echo "  health  Check application health"
    echo "  build   Build Docker image only"
    echo "  help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev     # Start development server"
    echo "  $0 prod    # Start production server"
    echo "  $0 logs    # View logs"
}

# Main script logic
case "${1:-help}" in
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    stop)
        stop
        ;;
    clean)
        clean
        ;;
    logs)
        logs
        ;;
    health)
        health
        ;;
    build)
        build
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
