#!/bin/bash

# Docker Quick Start Script for CAE
# This script helps users quickly start the application with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ASCII Art Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║   CAE - Conversational Analysis Engine    ║"
echo "║         Docker Quick Start                ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    print_info "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    print_info "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

print_status "Docker and Docker Compose are installed and running"

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        print_warning ".env file not found. Creating from env.example..."
        cp env.example .env
        print_warning "Please edit .env file with your API keys and configuration"
        print_info "Opening .env in default editor..."
        ${EDITOR:-nano} .env
    else
        print_error "Neither .env nor env.example found!"
        exit 1
    fi
else
    print_status ".env file found"
fi

# Ask user for deployment type
echo ""
print_info "Select deployment type:"
echo "1) Development (with hot-reload)"
echo "2) Production (optimized)"
echo -n "Enter choice [1-2]: "
read -r choice

case $choice in
    1)
        COMPOSE_FILE="docker-compose.yml"
        print_status "Starting in development mode..."
        ;;
    2)
        COMPOSE_FILE="docker-compose.prod.yml"
        print_status "Starting in production mode..."
        ;;
    *)
        print_error "Invalid choice. Defaulting to development mode."
        COMPOSE_FILE="docker-compose.yml"
        ;;
esac

# Build and start containers
print_status "Building Docker images..."
docker-compose -f $COMPOSE_FILE build

print_status "Starting containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 5

# Check if services are running
if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
    print_status "Services are running!"
    echo ""
    print_info "CAE is now available at:"
    echo -e "  ${GREEN}API:${NC} http://localhost:8000"
    echo -e "  ${GREEN}Docs:${NC} http://localhost:8000/docs"
    echo -e "  ${GREEN}Health:${NC} http://localhost:8000/health"
    echo ""
    print_info "Useful commands:"
    echo "  View logs:    docker-compose -f $COMPOSE_FILE logs -f"
    echo "  Stop:         docker-compose -f $COMPOSE_FILE down"
    echo "  Restart:      docker-compose -f $COMPOSE_FILE restart"
    echo ""
else
    print_error "Services failed to start. Check logs with:"
    echo "docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi 