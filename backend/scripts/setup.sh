#!/bin/bash

echo "🔧 Setting up RAG Video Chatbot Environment"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p chroma_db
mkdir -p downloads
mkdir -p logs

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"
fi

# Download embedding model cache
echo "🤖 Pre-downloading embedding model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your GOOGLE_API_KEY to .env"
echo "2. Run: uvicorn app.main:app --reload"
echo "3. Or use Docker: docker-compose up --build"