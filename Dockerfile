# syntax=docker/dockerfile:1

# == BUILD STAGE ==
# Pinning the version for reproducibility and security
ARG PYTHON_VERSION=3.13

# Note: change alpine to slim if you run into wheel/libc compilation issues
FROM astral/uv:python${PYTHON_VERSION}-alpine AS builder

# Keep the workdir consistent between stages to avoid subtle path bugs
WORKDIR /opt/app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

# Use BuildKit cache mounts to persist uv's download cache across builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy the rest of the project and install (ordering of instructions to take advantage of caching)
# for even more caching/reduce size, granularly copy the directories here and in the prod stage
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# == PROD STAGE ==
# multi-stage builds for reducing size of final image
FROM python:${PYTHON_VERSION}-alpine

# Create a separate non-root user for security
RUN adduser -u 1000 -h /opt/app -D app
USER app

WORKDIR /opt/app

ENV PATH="/opt/app/.venv/bin:$PATH" \
    FASTAPI_ENV=prod \
    PYTHONUNBUFFERED=1

COPY --from=builder --chown=app:app /opt/app .

EXPOSE 8000

ENTRYPOINT ["/opt/app/scripts/entrypoint.sh"]
CMD ["fastapi", "run"]
