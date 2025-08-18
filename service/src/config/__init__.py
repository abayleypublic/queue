from agents import set_default_openai_client, set_tracing_disabled, set_default_openai_api

from .config import Config

cfg = Config()

set_default_openai_client(cfg.openai.client)

# Ollama does not currently support the responses API
set_default_openai_api("chat_completions")
set_tracing_disabled(True)

