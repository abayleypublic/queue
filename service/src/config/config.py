from datetime import timedelta
from typing import Coroutine, Any, List, Dict, Type, Optional
from inspect import signature, Parameter

from openai import AsyncOpenAI
from agents import OpenAIProvider, Tool, function_tool, FunctionTool
from agents.mcp import  MCPServerStreamableHttp, MCPServerStreamableHttpParams
from pydantic import BaseModel, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio import activity
from temporalio.activity import _Definition
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters
from temporalio.contrib.openai_agents.workflow import activity_as_tool
from mcp import Tool as MCPTool

type_mapping: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}

class APIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="service_api_")

    port: int = 8003

class Property(BaseModel):
    name: str
    description: str
    title: str
    type: Type

    def docstring(self) -> str:
        return f"{self.name} ({str(self.type)}): {self.description}"

def test(foo:str, bar: str) -> str:
    pass

sig_test = signature(test)

[print(f"{k}: {v.kind}") for k, v in sig_test.parameters.items()]

print("signaturetest", sig_test.parameters)

class MCPConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="service_mcp_")

    address: str = "http://localhost:8002/mcp"
    _tools: List[MCPTool] = []

    @property
    def streamable_http(self) -> MCPServerStreamableHttp:
        return MCPServerStreamableHttp(
            params=MCPServerStreamableHttpParams(
                url=self.address
            ),
            use_structured_content=True
        )

    def _mcp_tool_to_activity(self, tool: MCPTool):
        input_properties: List[Property] = []

        for name, prop in tool.inputSchema.get("properties", {}).items():
            t = type_mapping.get(prop.get("type"), None)
            required = name in tool.inputSchema.get("required", [])

            input_properties.append(Property(
                name=name,
                description=prop.get("description", ""),
                title=prop.get("title", ""),
                type=t if required else Optional[t]
            ))

        t = type_mapping.get(prop.get("type"), None)
        required = name in tool.inputSchema.get("required", [])
        result: Property = Property(
            name="result",
            description="The result of the tool execution",
            title="Result",
            type=t if required else Optional[t]
        )

        async def run(*args, **kwargs):
            print("tool", tool.name)
            print("args", args)
            print("kwargs", kwargs)

            input = kwargs if len(args) == 0 else {prop.name: arg for prop, arg in zip(input_properties, args)}

            async with self.streamable_http as conn:
                print("calling tool", tool.name)
                res = await conn.call_tool(tool.name, input)
                print("res", res)
                return res

        setattr(run, "__name__", tool.name)

        sig = signature(run)
        sig = sig.replace(
            parameters=[
                Parameter(name=prop.name, kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=prop.type) for prop in input_properties
            ],
            return_annotation=result.type
        )
        setattr(run, "__signature__", sig)
        print("signaturexyz", sig.parameters)

        args_doc = "\n".join([prop.docstring() for prop in input_properties])
        setattr(run, "__doc__", f"""
            {tool.description}

            Args:
            {args_doc}

            Returns:
            {result.docstring()}
        """)

        # arg_types = [
        #     prop.type for prop in input_properties
        # ]

        # print("arg_types", arg_types)

        # setattr(
        #     run,
        #     "__temporal_activity_definition",
        #     _Definition(
        #         name=tool.name,
        #         fn=run,
        #         is_async=True,
        #         no_thread_cancel_exception=False,
        #         # arg_types=arg_types,
        #         # ret_type=result.type
        #     ),
        # )            

        _Definition._apply_to_callable(run, activity_name=tool.name)
        return run
    
    async def init_tools(self):
        async with self.streamable_http as conn:
            self._tools = await conn.list_tools()

    @property
    def activities(self):
        return [self._mcp_tool_to_activity(tool) for tool in self._tools]

class OpenAIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="service_openai_")

    api_key: str = "1234"
    api_base: str = "http://localhost:11434/v1"
    model: str = "gpt-oss:20b"
    # model: str = "llama3.2:3b"

    _client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
        return self._client


class TemporalConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="service_temporal_")

    host: str = "http://localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "queue"

class TemporalWorkerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="service_worker_")

class Config(BaseModel):
    api: APIConfig = APIConfig()
    mcp: MCPConfig = MCPConfig()
    openai: OpenAIConfig = OpenAIConfig()
    temporal: TemporalConfig = TemporalConfig()
    worker: TemporalWorkerConfig = TemporalWorkerConfig()

    @property
    def temporal_client(self) -> Coroutine[Any, Any, Client]:
        return Client.connect(
            f"{self.temporal.host}:{self.temporal.port}",
            namespace=self.temporal.namespace,
            data_converter=pydantic_data_converter,
            plugins=[OpenAIAgentsPlugin(
                model_params=ModelActivityParameters(
                    start_to_close_timeout=timedelta(seconds=90),
                    schedule_to_close_timeout=timedelta(seconds=500),
                    retry_policy=RetryPolicy(
                        backoff_coefficient=2.0,
                        maximum_attempts=5,
                        initial_interval=timedelta(seconds=1),
                    )
                ),
                model_provider=OpenAIProvider(
                    api_key=self.openai.api_key,
                    base_url=self.openai.api_base
                )
            )]
        ) 
