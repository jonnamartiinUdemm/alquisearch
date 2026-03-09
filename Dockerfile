# AlquiSearch España – Dockerfile
# Build: docker build -t alquisearch .
# Run:   docker run -p 8000:8000 -v $(pwd)/data:/app/data alquisearch

FROM python:3.11-slim

# System deps (lxml needs libxml2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# SQLite databases are stored in /app/data (mount a volume here for persistence)
ENV DB_DIR=/app/data
RUN mkdir -p /app/data

WORKDIR /app/backend

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
