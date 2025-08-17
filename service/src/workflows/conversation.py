from asyncio import Lock
from typing import List
from datetime import timedelta
from inspect import signature

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel
    from agents import (
        Agent, 
        Runner, 
        RunResult, 
        TResponseInputItem,
        RunConfig,
        FunctionTool
    )
    from temporalio.contrib.openai_agents.workflow import activity_as_tool

    from src.schema import Message, ConversationResultSchema
    from src.config import cfg

agent = Agent(
    name="Conversation Agent",
    model=cfg.openai.model,
    # tools=[activity_as_tool(tool) for tool in cfg.mcp.tools],
    instructions="You are a helpful assistant for a conversation. Respond to user messages.",
    tools=[activity_as_tool(tool, start_to_close_timeout=timedelta(seconds=10)) for tool in cfg.mcp.activities]

    # gpt-oss:20b doesn't work with structured outputs yet: https://github.com/ollama/ollama/issues/11691
    # I would like to use it though so I'm going to go for no structured output for now
    # output_type=ConversationResultSchema
)

if len(agent.tools) > 0:
    # print("params", agent.tools[0].params_json_schema)
    [print(signature(tool)) for tool in cfg.mcp.activities]

class ConversationArgs(BaseModel):
    user_id: str

@workflow.defn
class Conversation:
    def __init__(self):
        self._message: Message | None = None
        self._response: RunResult | None = None
        self._history: List[TResponseInputItem] = []
        self._processing: Lock = Lock()
        self._user: str = ""

    @staticmethod
    def id(user:str) -> str:
        return f"conversation_{user}"

    @workflow.query
    async def get_history(self) -> List[TResponseInputItem]:
        return self._history

    @workflow.update
    async def message(self, message: Message) -> ConversationResultSchema:
        async with self._processing:
            if self._message is not None:
                raise RuntimeError("message already set, cannot update.")

            self._message = message
            await workflow.wait_condition(lambda: self._message is None)
            return ConversationResultSchema(
                message=self._response.final_output_as(str)
            )

    @workflow.run
    async def run(self, args: ConversationArgs) -> str:
        workflow.logger.info(f"starting conversation for user {args.user_id}")
        self._user = args.user_id

        while True:
            await workflow.wait_condition(lambda: self._message is not None)
            workflow.logger.info(f"processing message: {self._message.text}")

            self._response = await Runner.run(
                agent,
                self._history + [
                    {
                        "role": "user",
                        "content": f"""
                            {self._message.text}
                        """
                    }
                ],
                run_config=RunConfig(
                    tracing_disabled=True
                )
            )

            # Apparently all the previous responses are included in this list? Interesting one.
            self._history = self._response.to_input_list()
            self._message = None
