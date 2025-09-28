import contextvars
from dataclasses import dataclass
from typing import Dict

@dataclass
class RequestContext():
    headers: Dict[str, str]

request: contextvars.ContextVar[RequestContext] = contextvars.ContextVar('request')