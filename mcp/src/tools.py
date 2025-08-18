from typing import Annotated, List

from fastmcp import FastMCP
from grpc import insecure_channel, RpcError
from loguru import logger

from .config import cfg
from .gen.queue_service_pb2 import GetQueueRequest, GetQueueResponse, SetQueueRequest, Entity
from .gen.queue_service_pb2_grpc import QueueStub

mcp = FastMCP("My MCP Server")

@mcp.tool
def add_to_queue(
    queue_id: Annotated[str, "The ID of the queue"],
    entity_id: Annotated[str, "The ID of the entity to add to the queue"],
    entity_name: Annotated[str, "The name of the entity to add to the queue"]) -> str:
    """
    add_to_queue adds an entity to the specified queue
    """

    with insecure_channel(cfg.backend.url) as channel:
        stub = QueueStub(channel)

        try:
            response: GetQueueResponse = stub.GetQueue(GetQueueRequest(id=queue_id))
        except RpcError as e:
            logger.error("failed to get queue: " + str(e))
            raise e

        try:
            _ = stub.SetQueue(SetQueueRequest(
                id=queue_id,
                entities=[*response.entities, Entity(
                    id=entity_id,
                    name=entity_name
                )]
            ))
        except RpcError as e:
            logger.error("failed to set queue: " + str(e))
            raise e

    return f"{entity_id} was successfully added to the queue"

@mcp.tool
def remove_from_queue(
    queue_id: Annotated[str, "The ID of the queue"],
    entity_id: Annotated[str, "The ID of the entity to remove from the queue"]
    ) -> str:
    """
    remove_from_queue removes an entity from the specified queue
    """

    with insecure_channel(cfg.backend.url) as channel:
        stub = QueueStub(channel)

        queue: List[Entity] = []
        try:
            response: GetQueueResponse = stub.GetQueue(GetQueueRequest(id=queue_id))
            for entity in response.entities:
                if entity.id != entity_id:
                    queue.append(entity)
        except RpcError as e:
            logger.error("failed to get queue: " + str(e))
            raise e

        try:
            _ = stub.SetQueue(SetQueueRequest(
                id=queue_id,
                entities=queue
            ))
        except RpcError as e:
            logger.error("failed to set queue: " + str(e))
            raise e

    return f"{entity_id} was successfully removed from the queue"
