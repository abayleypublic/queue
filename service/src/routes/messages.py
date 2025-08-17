from typing import List
from uuid import uuid4
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from agents import TResponseInputItem
from temporalio.client import WorkflowExecutionStatus, WorkflowHandle
from temporalio.service import RPCError
from temporalio.common import  WorkflowIDReusePolicy
from loguru import logger
from pydantic import BaseModel

from src.schema import Message, ConversationResultSchema
from src.config import cfg
from src.workflows.conversation import Conversation, ConversationArgs

router = APIRouter(prefix="/messages")

class MessageResponse(BaseModel):
    text: str
    actor: str

@router.get("", response_model=List[MessageResponse])
async def get_messages() -> List[MessageResponse]:
    client = await cfg.temporal_client
    handle = client.get_workflow_handle(Conversation.id("abayley"))
    history: List[TResponseInputItem] = await handle.query("get_history")

    output: List[MessageResponse] = []
    for message in history:
        content = message.get("content")
        if not content:
            continue

        actor = message.get("role")
        if not actor:
            continue

        match(actor):
            case "user":
                output.append(MessageResponse(
                    text=content.strip(),
                    actor=actor
                ))
            case "assistant":
                for c in content:
                    if not (c.get("text") and c.get("type")):
                        continue

                    if c.get("type") == "output_text":
                        output.append(MessageResponse(
                            text=c.get("text").strip(),
                            actor=actor
                        ))

    return output

@router.post("", response_model=ConversationResultSchema)
async def create_message(message: Message) -> ConversationResultSchema:
    client = await cfg.temporal_client

    handle: WorkflowHandle[Conversation, str] | None = None
    running = False
    try:
        handle = client.get_workflow_handle(Conversation.id("abayley"))
        desc = await handle.describe()
        running = desc.status == WorkflowExecutionStatus.RUNNING
    except RPCError as e:
        logger.error(f"error describing workflow: {e}")
    except Exception as e:
        logger.error(f"unexpected error describing workflow: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="an unexpected error occurred") from e

    if not running:
        handle = await client.start_workflow(
            Conversation.run,
            ConversationArgs(user_id="abayley"),
            id=Conversation.id("abayley"),
            task_queue=cfg.temporal.task_queue,
            id_reuse_policy=WorkflowIDReusePolicy.TERMINATE_IF_RUNNING,
        )

    result: ConversationResultSchema = await handle.execute_update(
        "message",
        message,
        id=str(uuid4())
    )

    return result