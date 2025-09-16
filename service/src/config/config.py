from datetime import timedelta
from typing import Coroutine, Any, List, Type, Optional
from inspect import signature, Parameter

from openai import AsyncOpenAI
from agents import OpenAIProvider
from agents.mcp import  MCPServerStreamableHttp, MCPServerStreamableHttpParams
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from temporalio.client import Client, TLSConfig
from temporalio.common import RetryPolicy
from temporalio.activity import _Definition
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters
from temporalio.contrib.opentelemetry import TracingInterceptor
from mcp import Tool as MCPTool

# as per https://json-schema.org/understanding-json-schema/reference/type
json_schema_types_to_python: dict[str, type] = {
    "string": str,
    "number": float,
    "object": dict,
    "array": list,
    "boolean": bool,
    "null": type(None)
}

class APIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="api_")

    host: str = "0.0.0.0"
    port: int = 8003

class Property(BaseModel):
    name: str
    description: str
    title: str
    type: Type

    def docstring(self) -> str:
        return f"{self.name} ({self.type.__name__}): {self.description}"

class MCPConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="mcp_")

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
        """
        _mcp_tool_to_activity converts an MCP tool to a Temporal activity. This is made necessary
        by the Temporal OpenAI agents integration currently being unable to consume dynamic
        MCP server calls. This function focusses on translating the MCP tool call into a standard
        function, complete with docstring and signature. It also wraps the function with the
        activity definition which enables simple translation to a function tool via the method
        supplied by the Temporal library.

        A potential enhnacement would be to use the `create_model` function from Pydantic but this
        adds some complexity to an already overly complex system.
        """

        input_properties: List[Property] = []

        for name, prop in tool.inputSchema.get("properties", {}).items():
            t = json_schema_types_to_python.get(prop.get("type"), None)
            required = name in tool.inputSchema.get("required", [])

            input_properties.append(Property(
                name=name,
                description=prop.get("description", ""),
                title=prop.get("title", ""),
                type=t if required else Optional[t]
            ))

        t = json_schema_types_to_python.get(prop.get("type"), None)
        required = name in tool.inputSchema.get("required", [])
        result: Property = Property(
            name="result",
            description=prop.get("description", "The result of the tool execution"),
            title="Result",
            type=t if required else Optional[t]
        )

        async def run(*args, **kwargs):
            """
            run simply calls the MCP tool with the provided arguments.
            """
            input = kwargs if len(args) == 0 else {prop.name: arg for prop, arg in zip(input_properties, args)}

            async with self.streamable_http as conn:
                return await conn.call_tool(tool.name, input)

        setattr(run, "__name__", tool.name)

        sig = signature(run)
        sig = sig.replace(
            parameters=[
                Parameter(name=prop.name, kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=prop.type) for prop in input_properties
            ],
            return_annotation=result.type
        )
        setattr(run, "__signature__", sig)

        args_doc = "\n".join([prop.docstring() for prop in input_properties])
        setattr(run, "__doc__", f"""
            {tool.description}

            Args:
            {args_doc}

            Returns:
            {result.docstring()}
        """)           

        _Definition._apply_to_callable(run, activity_name=tool.name)
        return run
    
    async def init_tools(self):
        """
        init_tools caches the tools available on the MCP server. It must be called
        prior to using the `activities` property.
        """
        async with self.streamable_http as conn:
            self._tools = await conn.list_tools()

    @property
    def activities(self):
        """
        activities returns a list of available tools as Temporal activities. `init_tools`
        must be called before accessing this property.
        """
        return [self._mcp_tool_to_activity(tool) for tool in self._tools]

class OpenAIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="openai_")

    api_key: str = "1234"
    api_base: str = "http://localhost:11434/v1"
    # model: str = "gpt-oss:20b"
    model: str = "llama3.2:3b"

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
    model_config = SettingsConfigDict(env_prefix="temporal_")

    host: str = "http://localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "queue"

    tls_cert: str | None = None
    tls_key: str | None = None
    tls_ca_cert: str | None = None
    tls_domain: str | None = None

    @property
    def tls_config(self) -> TLSConfig | None:
        if not (self.tls_cert and self.tls_key and self.tls_ca_cert):
            return None
        
        with open(self.tls_cert, "rb") as f:
            client_cert = f.read()

        with open(self.tls_key, "rb") as f:
            client_private_key = f.read()

        with open(self.tls_ca_cert, "rb") as f:
            server_root_ca_cert = f.read()

        return TLSConfig(
            client_cert=client_cert,
            client_private_key=client_private_key,
            server_root_ca_cert=server_root_ca_cert,
            domain=self.tls_domain,
        )

class TemporalWorkerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="worker_")

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
            tls=self.temporal.tls_config,
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
            )],
            interceptors=[TracingInterceptor()],
        ) 
