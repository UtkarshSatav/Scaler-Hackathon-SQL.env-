FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose HF Spaces default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the FastAPI server on port 7860 (HF Spaces default)
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
