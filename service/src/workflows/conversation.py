from asyncio import Lock
from typing import List, Optional
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel
    from agents import (
        Agent, 
        Runner, 
        RunResult, 
        TResponseInputItem,
        RunConfig,
    )
    from temporalio.contrib.openai_agents.workflow import activity_as_tool

    from src.schema import Message, ConversationResultSchema
    from src.config import cfg
    from src import context

class AuthContext(BaseModel):
    """Context object passed to Runner with auth headers."""
    auth_user: Optional[str] = None
    auth_email: Optional[str] = None
    auth_groups: Optional[str] = None

agent = Agent(
    name="Conversation Agent",
    model=cfg.openai.model,
    instructions="""
    You are a helpful assistant for a queue management system.
    You have access to tools that allow you to interact with queues, 
    such as adding entities to queues and retrieving the contents of 
    queues. Use these tools to assist users in managing their queues.

    If no queue is specified in the user's request, assume they are referring
    to the "default" queue.
    """,

    # The Temporal integration with OpenAI Agents does not currently support dynamic calls to MCP servers,
    # thus this workaround is necessary. It caches the tools at startup.
    # mcp_servers=[cfg.mcp.streamable_http],
    tools=[activity_as_tool(tool, start_to_close_timeout=timedelta(seconds=10)) for tool in cfg.mcp.activities]

    # gpt-oss:20b doesn't work with structured outputs yet: https://github.com/ollama/ollama/issues/11691
    # I would like to use it though so I'm going to go for no structured output for now
    # output_type=ConversationResultSchema
)

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
        # Store auth headers to pass to activities
        self._auth_user: Optional[str] = None
        self._auth_email: Optional[str] = None
        self._auth_groups: Optional[str] = None

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

            # Store auth headers from the message (deterministic - part of workflow input)
            self._auth_user = message.auth_user
            self._auth_email = message.auth_email
            self._auth_groups = message.auth_groups

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

            auth_context = AuthContext(
                auth_user=self._auth_user,
                auth_email=self._auth_email,
                auth_groups=self._auth_groups,
            )

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
                context=auth_context,  # Pass auth context to Runner
                run_config=RunConfig(
                    tracing_disabled=True
                )
            )

            # Apparently all the previous responses are included in this list? Interesting one.
            self._history = self._response.to_input_list()
            self._message = None
