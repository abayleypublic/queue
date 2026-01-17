from typing import Optional

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from uvicorn import Config, Server
from loguru import logger
import jwt

from .routes import messages, user
from .config import cfg
from . import context


def split_bearer_token(auth_header: str) -> Optional[str]:
    """
    Extract bearer token from Authorization header.
    """
    header_split = auth_header.split(" ")
    if len(header_split) != 2:
        return None
    
    if header_split[0].lower() != "bearer":
        return None

    return header_split[1]

class HeaderPropagationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture incoming headers and store them in contextvars.
    
    This enables headers to be accessed anywhere in the request lifecycle
    without explicit parameter passing.
    """
    async def dispatch(self, request: Request, call_next):
        logger.info(f"All request headers: {dict(request.headers)}")
        context.auth_user.set(request.headers.get('x-auth-request-user'))
        context.auth_email.set(request.headers.get('x-auth-request-email'))
        context.auth_groups.set(request.headers.get('x-auth-request-groups'))
        
        auth_header = request.headers.get('authorization')
        if auth_header and (token := split_bearer_token(auth_header)):
            try:
                claims = jwt.decode(token, options={"verify_signature": False})
                logger.info(f"JWT claims: {claims}")
                name = (
                    claims.get('name') or
                    claims.get('given_name') or
                    claims.get('nickname') or
                    claims.get('preferred_username')
                )
                logger.info(f"Extracted name: {name}")
                context.auth_name.set(name)
            except Exception as e:
                logger.warning(f"failed to decode JWT: {e}")
        else:
            logger.info(f"No valid Authorization header. auth_header present: {auth_header is not None}")

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