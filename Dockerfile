# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install build-time python packages
COPY pyproject.toml .
# We install dependencies to a temporary location
RUN pip install --no-cache-dir --prefix=/install \
    grpcio-tools \
    faiss-cpu \
    numpy \
    pydantic \
    grpcio \
    asyncio \
    pytest \
    pytest-asyncio \
    psycopg2-binary \
    # Add other common dependencies if they are in pyproject.toml
    .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY . .

# Ensure generated directory exists
RUN mkdir -p src/limbic/generated && touch src/limbic/generated/__init__.py

# Generate gRPC code at build time (in runtime stage)
RUN python -m grpc_tools.protoc -I./proto --python_out=./src/limbic/generated --grpc_python_out=./src/limbic/generated ./proto/limbic.proto

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:/app/sensorimotor/src

EXPOSE 50051

CMD ["python", "src/limbic/daemon.py"]
