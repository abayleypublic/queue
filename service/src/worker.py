from temporalio.worker import Worker
from loguru import logger

from .config import cfg
from .workflows import Conversation, agent

async def run_worker():
    logger.info("Starting Temporal worker...")
    client = await cfg.temporal_client
    await cfg.mcp.init_tools()

    worker = Worker(
        client,
        task_queue=cfg.temporal.task_queue,
        workflows=[
            Conversation
        ],
        activities=[
            *cfg.mcp.activities
        ],
    )

    await worker.run()