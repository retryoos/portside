# Papership.Ai API runtime — slim Python image with no native deps.
# Build context expected at apps/api (i.e. `docker build apps/api` from repo root).
# See notes/02-architecture.md §12 (App Runner deploy) and notes/16-aws-deploy.md.
#
# uv pin: 0.5.18 is the known-good standalone release we test against. Pin to a
# specific version (never `latest`) so App Runner rebuilds remain reproducible.

FROM python:3.12-slim AS runtime

# uv: fast, reproducible Python deps. Install via the official standalone binary
# so we don't depend on a Python-level pip self-install round trip.
ENV UV_VERSION=0.5.18
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh \
 && apt-get purge -y curl \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:${PATH}"

# Avoid .pyc clutter and unbuffered stdout for App Runner log streaming.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy lockfile + pyproject first so the dependency layer caches independently
# of the source. uv.lock is committed (apps/api/uv.lock).
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

# Copy the application package.
COPY portside_api /app/portside_api

# App Runner sets PORT; uvicorn listens on 0.0.0.0:8000 by default. Both work.
ENV PORT=8000
EXPOSE 8000

# CMD form (not ENTRYPOINT) so App Runner / Docker can override for ops.
CMD ["uv", "run", "--no-dev", "uvicorn", "portside_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
