from typing import Optional

from pydantic import BaseModel, Field

from .openai import OpenAISchema

class ConversationResultSchema(OpenAISchema):
    message: str = Field(
        ...,
        description="A response to relay to the user",
        default_factory=str
    )

class Message(BaseModel):
    """
    Message is a message sent by the user to the assistant.
    """
    text: str
    # Authentication headers passed from the API
    auth_user: Optional[str] = None
    auth_email: Optional[str] = None
    auth_groups: Optional[str] = None