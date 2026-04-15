#!/bin/bash

# Raskitoma QR - Deployment Script
# This script initializes the environment and starts the Docker container.

echo "🚀 Starting Raskitoma QR deployment..."

# 1. Initialize environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 .env file not found. Creating from .env.sample..."
    cp .env.sample .env
    echo "✅ .env created with standard values. You can edit it later if needed."
else
    echo "ℹ️  .env already exists, skipping initialization."
fi

# 2. Build and start the container
echo "🏗️  Building and starting Docker containers..."
docker compose up -d --build

# 3. Final summary
HOST_PORT=$(grep HOST_PORT .env | cut -d '=' -f2)
HOST_PORT=${HOST_PORT:-8060}

echo "✨ Deployment successful!"
echo "🌐 Application is available at: http://localhost:${HOST_PORT}"
echo "📝 Use 'docker compose logs -f' to view application logs."
