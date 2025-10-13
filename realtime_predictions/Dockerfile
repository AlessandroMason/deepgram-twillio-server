FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including curl for healthcheck)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models data

# Expose port (Render will use PORT env variable)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application with skip-checks for production
CMD python start_server.py --host 0.0.0.0 --port ${PORT:-8000} --skip-checks


