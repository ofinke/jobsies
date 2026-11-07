# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

# Installs git (needed for plugin system)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}"

# Create a non-root user and group
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/sh -d /app appuser

# Install third-party dependencies first
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# Copy the application source and install the project itself
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY docs ./docs
COPY configs ./configs
COPY startup.sh ./
RUN chmod +x startup.sh

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Create data directory and ensure proper ownership
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/app/startup.sh"]
CMD ["worker"]
