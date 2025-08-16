from src.tools import mcp
from src import cfg

if __name__ == "__main__":
    mcp.run(
        transport=cfg.server.transport,
        host=cfg.server.host,
        port=cfg.server.port
    )
