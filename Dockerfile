FROM python:3.11-slim as builder

# Install dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

# Generate gRPC
RUN python -m grpc_tools.protoc -I./proto --python_out=./src/limbic/generated --grpc_python_out=./src/limbic/generated ./proto/limbic.proto

EXPOSE 50051

CMD ["python", "src/limbic/daemon.py"]
