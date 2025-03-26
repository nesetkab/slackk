FROM python:3.11-slim

WORKDIR /app

# Install build dependencies and curl (for health checks)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/ || exit 1

# Start Gunicorn with a longer timeout
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 300 wsgi:application