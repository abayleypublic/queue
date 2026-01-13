from typing import Annotated, List

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from grpc import insecure_channel, RpcError
from loguru import logger

from .config import cfg
from .gen.queue_service_pb2 import GetQueueRequest, GetQueueResponse, SetQueueRequest, Entity
from .gen.queue_service_pb2_grpc import QueueStub

mcp = FastMCP("My MCP Server")


# This translates to a string but only because I would prefer to spend the effort on
# other things for now
@mcp.tool
def get_queue(
    queue_id: Annotated[str, "The ID of the queue"]
) -> str:
    """
    get_queue retrieves the specified queue. The response includes entity IDs and names.
    """
    
    headers = get_http_headers()

    with insecure_channel(cfg.backend.url) as channel:
        stub = QueueStub(channel)

        try:
            response: GetQueueResponse = stub.GetQueue(
                GetQueueRequest(id=queue_id), 
                metadata=tuple((key, value) for key, value in headers.items())
            )
        except RpcError as e:
            logger.error("failed to get queue: " + str(e))
            raise e

    if not response.entities:
        return "No entities in queue"
    
    # Return formatted list showing both ID and name
    entities_list = [f"{entity.name} (ID: {entity.id})" for entity in response.entities]
    return "Queue contents:\n" + "\n".join(f"  - {item}" for item in entities_list)

@mcp.tool
def add_to_queue(
    queue_id: Annotated[str, "The ID of the queue"],
    entity_id: Annotated[str, "The ID of the entity to add to the queue. Must be a valid, non-empty identifier."],
    entity_name: Annotated[str, "The name of the entity to add to the queue"]) -> str:
    """
    add_to_queue adds an entity to the specified queue. A valid entity_id is required.
    """

    if not entity_id or entity_id.strip() == "":
        error_msg = "entity_id is required and cannot be empty. Please provide a valid identifier for the entity."
        logger.error(error_msg)
        raise ValueError(error_msg)

    headers_dict = get_http_headers()
    headers = tuple((key, value) for key, value in headers_dict.items())

    with insecure_channel(cfg.backend.url) as channel:
        stub = QueueStub(channel)

        try:
            response, _ = stub.GetQueue.with_call(
                GetQueueRequest(id=queue_id),
                metadata=headers
            )
        except RpcError as e:
            logger.error("failed to get queue: " + str(e))
            raise e

        try:
            _, _ = stub.SetQueue.with_call(
                SetQueueRequest(
                    id=queue_id,
                    entities=[*response.entities, Entity(
                        id=entity_id,
                        name=entity_name
                    )]
                ),
                metadata=headers
            )
        except RpcError as e:
            logger.error("failed to set queue: " + str(e))
            raise e

    return f"Entity '{entity_name}' (ID: {entity_id}) was successfully added to the queue"

@mcp.tool
def remove_from_queue(
    queue_id: Annotated[str, "The ID of the queue"],
    entity_id: Annotated[str, "The ID of the entity to remove from the queue"]
    ) -> str:
    """
    remove_from_queue removes an entity from the specified queue
    """

    headers = tuple((key, value) for key, value in get_http_headers().items())

    with insecure_channel(cfg.backend.url) as channel:
        stub = QueueStub(channel)

        queue: List[Entity] = []
        try:
            response: GetQueueResponse = stub.GetQueue(
                GetQueueRequest(id=queue_id),
                metadata=headers
            )
            for entity in response.entities:
                if entity.id != entity_id:
                    queue.append(entity)
        except RpcError as e:
            logger.error("failed to get queue: " + str(e))
            raise e

        try:
            _ = stub.SetQueue(
                SetQueueRequest(
                    id=queue_id,
                    entities=queue
                ),
                metadata=headers
            )
        except RpcError as e:
            logger.error("failed to set queue: " + str(e))
            raise e

    return f"{entity_id} was successfully removed from the queue"
