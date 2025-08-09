"""
PyFrame Plugin System

Provides extensible plugin architecture allowing third-party extensions
for authentication, payments, analytics, caching, and custom functionality.
"""

from .plugin import Plugin, PluginManager, PluginHook
from .hooks import HookManager, hook, before, after
from .auth_plugin import AuthPlugin
from .cache_plugin import CachePlugin
from .analytics_plugin import AnalyticsPlugin

__all__ = [
    "Plugin", 
    "PluginManager", 
    "PluginHook",
    "HookManager", 
    "hook", 
    "before", 
    "after",
    "AuthPlugin",
    "CachePlugin",
    "AnalyticsPlugin"
]
