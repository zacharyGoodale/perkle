FROM python:3.12-slim

WORKDIR /app

# Install SQLCipher runtime/build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libsqlcipher-dev \
        sqlcipher \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run with uvicorn via uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
