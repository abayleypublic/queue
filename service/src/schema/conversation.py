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