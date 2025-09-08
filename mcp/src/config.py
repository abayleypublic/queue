from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class BackendConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="backend_")

    host: str = "localhost"
    port: int = 8001

    @property
    def url(self) -> str:
        return f"{self.host}:{self.port}"

    
class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="server_")

    transport: str = "http"
    host: str = "localhost"
    port: int = 8002


class Config(BaseModel):
    server: ServerConfig = ServerConfig()
    backend: BackendConfig = BackendConfig()

cfg = Config()