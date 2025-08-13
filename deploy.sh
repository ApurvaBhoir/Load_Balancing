#!/bin/bash

# Ritter Sport Production Planner - Docker Deployment Script

set -e

echo "🐳 Ritter Sport Production Planner - Docker Deployment"
echo "======================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose is not available. Please install Docker Compose:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Using: $COMPOSE_CMD"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/processed data/reports logs

# Set proper permissions
chmod 755 data logs

# Function to build and start the application
deploy() {
    echo "🏗️  Building Docker image..."
    $COMPOSE_CMD build

    echo "🚀 Starting application..."
    $COMPOSE_CMD up -d

    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "🌐 Application available at: http://localhost:8501"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs:    $COMPOSE_CMD logs -f"
    echo "   Stop app:     $COMPOSE_CMD down"
    echo "   Restart:      $COMPOSE_CMD restart"
    echo "   Shell access: $COMPOSE_CMD exec ritter-sport-planner /bin/bash"
}

# Function to stop the application
stop() {
    echo "🛑 Stopping application..."
    $COMPOSE_CMD down
    echo "✅ Application stopped"
}

# Function to show logs
logs() {
    echo "📄 Showing application logs..."
    $COMPOSE_CMD logs -f
}

# Function to show status
status() {
    echo "📊 Application status:"
    $COMPOSE_CMD ps
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy"|"start"|"up")
        deploy
        ;;
    "stop"|"down")
        stop
        ;;
    "logs")
        logs
        ;;
    "status"|"ps")
        status
        ;;
    "restart")
        stop
        sleep 2
        deploy
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy/start/up    Build and start the application (default)"
        echo "  stop/down          Stop the application"
        echo "  restart            Stop and start the application"
        echo "  logs               Show application logs"
        echo "  status/ps          Show application status"
        echo "  help               Show this help message"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' to see available commands"
        exit 1
        ;;
esac
