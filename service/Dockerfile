FROM python:3.14.2-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-cache

CMD ["uv", "run", "main.py"]