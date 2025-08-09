"""
PyFrame Server Module

Handles request processing, context detection, and adaptive responses
based on client capabilities and preferences.
"""

from .context import RequestContext, ClientContext, AdaptiveRenderer
from .dev_server import DevServer

__all__ = ["RequestContext", "ClientContext", "AdaptiveRenderer", "DevServer"]
