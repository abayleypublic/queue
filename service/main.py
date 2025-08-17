import asyncio
import logging

from loguru import logger
from src.worker import run_worker
from src.api import run_api

logging.basicConfig(level=logging.INFO)
    
async def main():
    logger.info("Starting service...")

    await asyncio.wait(
        [run_worker(), run_api()],
        return_when=asyncio.FIRST_COMPLETED,
        )

    logger.info("Service stopped.")

if __name__ == "__main__":
    asyncio.run(main())
