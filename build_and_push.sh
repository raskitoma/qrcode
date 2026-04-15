#!/bin/bash

# QR Code Generator - Build and Push Script
# This script builds the image for multiple architectures (AMD64 and ARM64)
# and pushes it to your Docker Hub repository.

IMAGE_NAME="raskitoma/qrcode"
TAG="latest"

echo "🛠️  Starting multi-arch build for ${IMAGE_NAME}:${TAG}..."

# Ensure we are using a buildx builder that supports multiple platforms
BUILDER_NAME="qrcode-builder"
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo "🏗️  Creating new buildx builder..."
    docker buildx create --name "$BUILDER_NAME" --use
else
    docker buildx use "$BUILDER_NAME"
fi

# Build and Push
# --platform specifies the target architectures
# --push tells buildx to push the manifest to Docker Hub
echo "🚀 Building and pushing to Docker Hub..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t "${IMAGE_NAME}:${TAG}" \
    --push .

echo "✅ Multi-arch build and push complete!"
echo "🌐 Image available at: https://hub.docker.com/r/${IMAGE_NAME}"
