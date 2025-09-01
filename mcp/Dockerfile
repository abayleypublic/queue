FROM python:3.10.18-alpine3.22

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-cache

CMD ["uv", "run", "main.py"]