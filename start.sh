#!/bin/bash

echo "🚀 Starting RAG Video Chatbot..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp backend/.env.example backend/.env
    echo "✅ Please edit backend/.env and add your API keys"
    exit 1
fi

# Start services
echo "📦 Building and starting containers..."
docker-compose up --build

# Or run locally without Docker
# echo "🐍 Starting backend..."
# cd backend && uvicorn app.main:app --reload --port 8000 &
# echo "⚛️  Starting frontend..."
# cd frontend && npm run dev