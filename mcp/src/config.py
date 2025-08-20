from pydantic import BaseModel
from pydantic_settings import BaseSettings

class BackendConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8001

    @property
    def url(self) -> str:
        return f"{self.host}:{self.port}"

    class Config:
        env_prefix = "mcp_backend_"

class ServerConfig(BaseSettings):
    transport: str = "http"
    host: str = "localhost"
    port: int = 8002

    class Config:
        env_prefix = "mcp_"

class Config(BaseModel):
    server: ServerConfig = ServerConfig()
    backend: BackendConfig = BackendConfig()

cfg = Config()