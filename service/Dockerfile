FROM python:3.10.18-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-cache
RUN uv pip install opentelemetry-distro opentelemetry-exporter-otlp
RUN uv run opentelemetry-bootstrap -a requirements | uv pip install --requirement -

CMD ["uv", "run", "opentelemetry-instrument", "python", "main.py"]