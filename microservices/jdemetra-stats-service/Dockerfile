# Base image
FROM python:3.12-slim as base

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

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]