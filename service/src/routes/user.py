from typing import Optional, Dict, List
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from grpc import insecure_channel, RpcError
from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError
from loguru import logger

from src import context
from src.config import cfg
from src.workflows.conversation import Conversation
from src.routes.messages import ALLOWED_QUEUES
from src.gen.queue_service_pb2 import GetQueueRequest, SetQueueRequest, GetQueueResponse
from src.gen.queue_service_pb2_grpc import QueueStub

router = APIRouter(prefix="/user")


class UserResponse(BaseModel):
    """User information extracted from authentication headers."""
    name: Optional[str] = None
    username: Optional[str] = None  # Contains preferred_username or email from Auth0
    email: Optional[str] = None
    groups: Optional[str] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user() -> UserResponse:
    """
    Get the current authenticated user's information from request headers.
    
    Returns user details that were propagated from the authentication gateway.
    """
    return UserResponse(
        name=context.get_auth_name(),
        username=context.get_auth_user(),
        email=context.get_auth_email(),
        groups=context.get_auth_groups()
    )


class QueueData(BaseModel):
    """Data for a single queue."""
    queue_id: str
    entities: List[Dict[str, str]]


class UserDataResponse(BaseModel):
    """GDPR data export response."""
    queues: List[QueueData]
    workflow_status: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None


@router.get("/me/download", response_model=UserDataResponse)
async def download_user_data() -> UserDataResponse:
    """
    GDPR data export endpoint - returns all user data across all queues.
    
    This includes:
    - All entities where the user's email is the entity ID
    - Temporal workflow status
    - Conversation history (messages and responses)
    """
    email = context.get_auth_email()
    if not email:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="user email is required"
        )
    
    logger.info(f"GDPR export requested for user: {email}")
    
    queues_data: List[QueueData] = []
    
    # Query all known queues for user's entities
    try:
        with insecure_channel(cfg.backend.url) as channel:
            stub = QueueStub(channel)
            
            for queue_id in ALLOWED_QUEUES:
                try:
                    response = stub.GetQueue(
                        GetQueueRequest(id=queue_id),
                        metadata=(
                            ("x-auth-request-email", email),
                        )
                    )
                    
                    # Filter entities that belong to this user (entity.id == user email)
                    user_entities = [
                        {"id": entity.id, "name": entity.name}
                        for entity in response.entities
                        if entity.id == email
                    ]
                    
                    if user_entities:
                        queues_data.append(QueueData(
                            queue_id=queue_id,
                            entities=user_entities
                        ))
                except RpcError as e:
                    logger.error(f"failed to get queue {queue_id}: {e}")
                    raise HTTPException(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail=f"failed to retrieve queue {queue_id}"
                    )
                    
    except Exception as e:
        logger.error(f"failed to query backend: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="failed to retrieve queue data"
        )
    
    # Get workflow status
    workflow_status = None
    conversation_history = None
    try:
        client = await cfg.temporal_client
        handle = client.get_workflow_handle(Conversation.id(email))
        desc = await handle.describe()
        workflow_status = desc.status.name
        
        if desc.status == WorkflowExecutionStatus.RUNNING:
            try:
                history = await handle.query("get_history")
                conversation_history = history 
            except Exception as e:
                logger.warning(f"failed to get conversation history: {e}")
    except RPCError:
        workflow_status = "NOT_FOUND"
    except Exception as e:
        logger.warning(f"failed to get workflow status: {e}")
        workflow_status = "UNKNOWN"
    
    logger.info(f"GDPR export completed for user: {email}")
    return UserDataResponse(
        queues=queues_data,
        workflow_status=workflow_status,
        conversation_history=conversation_history
    )


class DeleteUserDataResponse(BaseModel):
    """GDPR deletion response."""
    success: bool
    message: str
    deleted_from_queues: List[str]


@router.delete("/me", response_model=DeleteUserDataResponse)
async def delete_user_data() -> DeleteUserDataResponse:
    """
    GDPR data deletion endpoint - deletes all user data across all queues.
    
    This includes:
    - Terminating any running Temporal workflows
    - Removing user entities from all queues
    """
    email = context.get_auth_email()
    if not email:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="user email is required"
        )
    
    logger.info(f"GDPR deletion requested for user: {email}")
    
    # Terminate workflow if running
    workflow_terminated = False
    try:
        client = await cfg.temporal_client
        handle = client.get_workflow_handle(Conversation.id(email))
        desc = await handle.describe()
        if desc.status == WorkflowExecutionStatus.RUNNING:
            await handle.terminate(reason="GDPR user data deletion")
            workflow_terminated = True
            logger.info(f"terminated workflow for user: {email}")
    except RPCError:
        logger.info(f"no running workflow found for user: {email}")
    except Exception as e:
        logger.error(f"failed to terminate workflow: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="failed to terminate user workflow"
        )
    
    # Delete user entities from all queues
    deleted_from_queues: List[str] = []
    try:
        with insecure_channel(cfg.backend.url) as channel:
            stub = QueueStub(channel)
            
            for queue_id in ALLOWED_QUEUES:
                try:
                    # Get current queue
                    response: GetQueueResponse = stub.GetQueue(
                        GetQueueRequest(id=queue_id),
                        metadata=(
                            ("x-auth-request-email", email),
                        )
                    )

                    # Filter out user's entities
                    remaining_entities = [
                        entity for entity in response.entities
                        if entity.id.replace(" ", "") != email.replace(" ", "")
                    ]
                    
                    # Update queue if any entities were removed
                    if len(remaining_entities) < len(response.entities):
                        stub.SetQueue(
                            SetQueueRequest(
                                id=queue_id,
                                entities=remaining_entities
                            ),
                            metadata=(
                                ("x-auth-request-email", email),
                            )
                        )
                        deleted_from_queues.append(queue_id)
                        logger.info(f"removed user entity from queue: {queue_id}")
                        
                except RpcError as e:
                    logger.error(f"failed to process queue {queue_id}: {e}")
                    raise HTTPException(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail=f"failed to delete from queue {queue_id}"
                    )
                    
    except Exception as e:
        logger.error(f"unexpected error deleting user data: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="failed to delete user data"
        )
    
    message = "User data deleted successfully"
    if workflow_terminated:
        message += " (workflow terminated)"
    if deleted_from_queues:
        message += f" from queues: {', '.join(deleted_from_queues)}"
    
    logger.info(f"GDPR deletion completed for user: {email}")
    return DeleteUserDataResponse(
        success=True,
        message=message,
        deleted_from_queues=deleted_from_queues
    )
