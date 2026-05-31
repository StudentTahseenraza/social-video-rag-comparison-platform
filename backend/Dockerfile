FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for video processing and Whisper
RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for faster-whisper
RUN pip install --no-cache-dir faster-whisper==0.10.0 ctranslate2==3.20.0

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/rag_chatbot /app/downloads /root/.cache/whisper

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_DISABLE_TELEMETRY=1

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]