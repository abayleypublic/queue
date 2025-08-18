from pydantic import BaseModel, ConfigDict

class OpenAISchema(BaseModel):
    model_config = ConfigDict(extra="forbid")