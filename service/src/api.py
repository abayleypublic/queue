from fastapi import FastAPI
from uvicorn import Config, Server
from loguru import logger

from .routes import messages
from .config import cfg

app = FastAPI()
app.include_router(messages.router)

async def run_api():
    logger.info("starting API server...")
    config = Config(app=app, host=cfg.api.host, port=cfg.api.port, log_level="info")
    server = Server(config)
    await server.serve()