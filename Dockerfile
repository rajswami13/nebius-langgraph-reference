FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
# NEBIUS_API_KEY and OTEL_EXPORTER_OTLP_ENDPOINT are injected at runtime (k8s Secret / env)
ENTRYPOINT ["nebius-agent"]
