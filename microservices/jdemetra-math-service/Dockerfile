# Base image
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY ../jdemetra-common /jdemetra-common

# Install dependencies
RUN pip install --no-cache-dir -e /jdemetra-common && \
    pip install --no-cache-dir -e .

# Service image
FROM base as service

# Copy application code
COPY src/ ./src/
COPY proto/ ./proto/

# Generate proto files
RUN python src/generate_proto.py

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose gRPC port
EXPOSE 50051

# Health check using grpc_health_probe
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import grpc; channel = grpc.insecure_channel('localhost:50051'); channel.channel_ready()"

# Run the service
CMD ["python", "-m", "src.server"]