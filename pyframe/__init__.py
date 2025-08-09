"""
PyFrame - A Full-Stack Python Web Framework

A modern, reactive web framework that allows developers to write both 
frontend and backend entirely in Python, with automatic compilation to 
efficient JavaScript for the browser.

Key Features:
- Unified Python frontend and backend development
- Automatic context-aware adaptivity
- Zero-boilerplate data layer with auto-generated APIs
- Built-in reactive live updates
- Plugin-based extensibility
- Progressive enhancement and accessibility
- Modern deployment flexibility
"""

__version__ = "0.1.0"
__author__ = "PyFrame Team"
__license__ = "MIT"

from .core.app import PyFrameApp, PyFrameConfig
from .core.component import Component, StatefulComponent, State
from .core.routing import Route, Router
from .data.models import Model, Field
from .plugins.plugin import Plugin
from .server.context import RequestContext

__all__ = [
    "PyFrameApp",
    "PyFrameConfig",
    "Component",
    "StatefulComponent", 
    "State",
    "Route",
    "Router", 
    "Model",
    "Field",
    "Plugin",
    "RequestContext"
]
