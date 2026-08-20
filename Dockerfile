FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
# Create dummy src structure for pip install to work and cache deps
RUN mkdir -p src/pyqueue && touch src/pyqueue/__init__.py
RUN pip install --no-cache-dir .

# Install application
COPY src src
RUN pip install --no-cache-dir .

# Copy rest of the application
COPY . .
