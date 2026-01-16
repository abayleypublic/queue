from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from uvicorn import Config, Server
from loguru import logger

from .routes import messages, user
from .config import cfg
from . import context


class HeaderPropagationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture incoming headers and store them in contextvars.
    
    This enables headers to be accessed anywhere in the request lifecycle
    without explicit parameter passing.
    """
    async def dispatch(self, request: Request, call_next):
        # Extract authentication headers from gateway
        context.auth_user.set(request.headers.get('x-auth-request-user'))
        context.auth_email.set(request.headers.get('x-auth-request-email'))
        context.auth_groups.set(request.headers.get('x-auth-request-groups'))

        response = await call_next(request)
        return response


app = FastAPI()
app.add_middleware(HeaderPropagationMiddleware)
app.include_router(messages.router)
app.include_router(user.router)

async def run_api():
    logger.info("starting API server...")
    config = Config(app=app, host=cfg.api.host, port=cfg.api.port, log_level="info")
    server = Server(config)
    await server.serve()