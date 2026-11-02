# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

ARG APP_NAME

WORKDIR /app

# Install system build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen

# Install PyInstaller inside uv environment
RUN uv run pip install pyinstaller

# Copy full project
COPY . .

# Build binary
RUN uv run pyinstaller --onefile --name ${APP_NAME} main.py


# ---------- Stage 2: Runtime ----------
FROM debian:bookworm-slim

ARG APP_NAME
ARG RELEASE_VERSION
ARG BUILD_TIME

ENV RELEASE_VERSION=${RELEASE_VERSION}
ENV BUILD_TIME=${BUILD_TIME}
ENV APP_NAME=${APP_NAME}
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
WORKDIR /app

# Copy compiled binary
COPY --from=builder /app/dist/${APP_NAME} /app/${APP_NAME}

RUN chmod +x /app/${APP_NAME}

ENTRYPOINT ["/bin/sh", "-c", "/app/$APP_NAME"]