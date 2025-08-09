"""
Core Plugin System

Base plugin architecture with lifecycle management, dependency resolution,
and hook system for extending PyFrame functionality.
"""

import json
import importlib
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    ERROR = "error"


class HookType(Enum):
    """Types of plugin hooks"""
    BEFORE_REQUEST = "before_request"
    AFTER_REQUEST = "after_request"
    BEFORE_RENDER = "before_render"
    AFTER_RENDER = "after_render"
    BEFORE_COMPONENT_MOUNT = "before_component_mount"
    AFTER_COMPONENT_MOUNT = "after_component_mount"
    BEFORE_STATE_CHANGE = "before_state_change"
    AFTER_STATE_CHANGE = "after_state_change"
    BEFORE_MODEL_SAVE = "before_model_save"
    AFTER_MODEL_SAVE = "after_model_save"
    CUSTOM = "custom"


@dataclass
class PluginInfo:
    """Plugin metadata and information"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    pyframe_version: str = ">=0.1.0"
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    license: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginInfo':
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            dependencies=data.get("dependencies", []),
            pyframe_version=data.get("pyframe_version", ">=0.1.0"),
            tags=data.get("tags", []),
            homepage=data.get("homepage"),
            license=data.get("license")
        )


class PluginHook:
    """Represents a plugin hook registration"""
    
    def __init__(self, hook_type: HookType, callback: Callable,
                 priority: int = 100, conditions: Dict[str, Any] = None):
        self.hook_type = hook_type
        self.callback = callback
        self.priority = priority  # Lower numbers = higher priority
        self.conditions = conditions or {}
        self.plugin_name: Optional[str] = None
        
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if hook should execute based on conditions"""
        if not self.conditions:
            return True
            
        for key, expected_value in self.conditions.items():
            if key not in context or context[key] != expected_value:
                return False
                
        return True
        
    async def execute(self, context: Dict[str, Any], *args, **kwargs) -> Any:
        """Execute the hook callback"""
        try:
            if self.should_execute(context):
                if asyncio.iscoroutinefunction(self.callback):
                    return await self.callback(context, *args, **kwargs)
                else:
                    return self.callback(context, *args, **kwargs)
        except Exception as e:
            print(f"Error executing hook {self.hook_type.value} from {self.plugin_name}: {e}")
            raise


class Plugin(ABC):
    """
    Base class for all PyFrame plugins.
    
    Provides lifecycle management, configuration, and integration
    with the PyFrame application framework.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.state = PluginState.UNLOADED
        self.app = None
        self.hooks: List[PluginHook] = []
        self._info: Optional[PluginInfo] = None
        
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Plugin metadata and information"""
        pass
        
    @abstractmethod
    async def initialize(self, app) -> None:
        """Initialize the plugin with the application"""
        pass
        
    async def activate(self) -> None:
        """Activate the plugin (called after initialization)"""
        self.state = PluginState.ACTIVE
        
    async def deactivate(self) -> None:
        """Deactivate the plugin"""
        self.state = PluginState.DEACTIVATING
        
        # Unregister all hooks
        if self.app and hasattr(self.app, 'plugin_manager'):
            for hook in self.hooks:
                self.app.plugin_manager.unregister_hook(hook)
                
        self.state = PluginState.LOADED
        
    async def configure(self, config: Dict[str, Any]) -> None:
        """Update plugin configuration"""
        self.config.update(config)
        
    def register_hook(self, hook_type: HookType, callback: Callable,
                     priority: int = 100, conditions: Dict[str, Any] = None) -> PluginHook:
        """Register a hook with the application"""
        hook = PluginHook(hook_type, callback, priority, conditions)
        hook.plugin_name = self.info.name
        self.hooks.append(hook)
        
        if self.app and hasattr(self.app, 'plugin_manager'):
            self.app.plugin_manager.register_hook(hook)
            
        return hook
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
        
    def get_state(self) -> PluginState:
        """Get current plugin state"""
        return self.state


class PluginManager:
    """
    Manages plugin lifecycle, dependencies, and hook execution.
    
    Provides plugin discovery, loading, initialization, and coordination
    across the PyFrame application.
    """
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.hooks: Dict[HookType, List[PluginHook]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.load_order: List[str] = []
        
    def register(self, plugin: Plugin) -> None:
        """Register a plugin instance"""
        plugin_name = plugin.info.name
        
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered")
            
        self.plugins[plugin_name] = plugin
        self._build_dependency_graph()
        
        print(f"Plugin registered: {plugin_name} v{plugin.info.version}")
        
    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            
            # Deactivate plugin
            import asyncio
            asyncio.create_task(plugin.deactivate())
            
            # Remove from registry
            del self.plugins[plugin_name]
            self._build_dependency_graph()
            
            print(f"Plugin unregistered: {plugin_name}")
            
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get plugin instance by name"""
        return self.plugins.get(plugin_name)
        
    def get_active_plugins(self) -> List[Plugin]:
        """Get list of active plugins"""
        return [plugin for plugin in self.plugins.values() 
                if plugin.state == PluginState.ACTIVE]
        
    async def initialize_all(self, app) -> None:
        """Initialize all plugins in dependency order"""
        
        # Resolve load order
        self._resolve_load_order()
        
        # Initialize plugins
        for plugin_name in self.load_order:
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name]
                
                try:
                    plugin.state = PluginState.INITIALIZING
                    plugin.app = app
                    
                    # Apply configuration
                    if plugin_name in self.plugin_configs:
                        await plugin.configure(self.plugin_configs[plugin_name])
                        
                    # Initialize plugin
                    await plugin.initialize(app)
                    plugin.state = PluginState.LOADED
                    
                    # Activate plugin
                    await plugin.activate()
                    
                    print(f"Plugin initialized: {plugin_name}")
                    
                except Exception as e:
                    plugin.state = PluginState.ERROR
                    print(f"Error initializing plugin {plugin_name}: {e}")
                    
    async def deactivate_all(self) -> None:
        """Deactivate all plugins"""
        
        # Reverse load order for deactivation
        for plugin_name in reversed(self.load_order):
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name]
                
                if plugin.state == PluginState.ACTIVE:
                    try:
                        await plugin.deactivate()
                        print(f"Plugin deactivated: {plugin_name}")
                    except Exception as e:
                        print(f"Error deactivating plugin {plugin_name}: {e}")
                        
    def register_hook(self, hook: PluginHook) -> None:
        """Register a plugin hook"""
        if hook.hook_type not in self.hooks:
            self.hooks[hook.hook_type] = []
            
        self.hooks[hook.hook_type].append(hook)
        
        # Sort by priority (lower numbers first)
        self.hooks[hook.hook_type].sort(key=lambda h: h.priority)
        
    def unregister_hook(self, hook: PluginHook) -> None:
        """Unregister a plugin hook"""
        if hook.hook_type in self.hooks:
            self.hooks[hook.hook_type].remove(hook)
            
    async def execute_hooks(self, hook_type: HookType, context: Dict[str, Any],
                          *args, **kwargs) -> List[Any]:
        """Execute all hooks of a specific type"""
        results = []
        
        if hook_type in self.hooks:
            for hook in self.hooks[hook_type]:
                try:
                    result = await hook.execute(context, *args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"Error executing hook {hook_type.value}: {e}")
                    
        return results
        
    def load_from_directory(self, plugin_dir: str) -> None:
        """Load plugins from a directory"""
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            return
            
        for item in plugin_path.iterdir():
            if item.is_dir():
                self._load_plugin_from_path(item)
                
    def _load_plugin_from_path(self, plugin_path: Path) -> None:
        """Load a plugin from a specific path"""
        
        # Look for plugin.json metadata
        metadata_file = plugin_path / "plugin.json"
        if not metadata_file.exists():
            return
            
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            plugin_info = PluginInfo.from_dict(metadata)
            
            # Look for main plugin file
            main_file = plugin_path / "main.py"
            if not main_file.exists():
                print(f"Plugin main.py not found in {plugin_path}")
                return
                
            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_info.name}", 
                main_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class
            if hasattr(module, 'plugin_class'):
                plugin_class = module.plugin_class
                plugin = plugin_class()
                self.register(plugin)
            else:
                print(f"No plugin_class found in {main_file}")
                
        except Exception as e:
            print(f"Error loading plugin from {plugin_path}: {e}")
            
    def _build_dependency_graph(self) -> None:
        """Build dependency graph for plugins"""
        self.dependency_graph.clear()
        
        for plugin_name, plugin in self.plugins.items():
            dependencies = set(plugin.info.dependencies)
            self.dependency_graph[plugin_name] = dependencies
            
    def _resolve_load_order(self) -> None:
        """Resolve plugin load order based on dependencies"""
        self.load_order.clear()
        visited = set()
        temp_visited = set()
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {plugin_name}")
            if plugin_name in visited:
                return
                
            temp_visited.add(plugin_name)
            
            # Visit dependencies first
            if plugin_name in self.dependency_graph:
                for dependency in self.dependency_graph[plugin_name]:
                    if dependency in self.plugins:
                        visit(dependency)
                    else:
                        print(f"Warning: Plugin {plugin_name} depends on {dependency} which is not available")
                        
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            self.load_order.append(plugin_name)
            
        # Visit all plugins
        for plugin_name in self.plugins:
            if plugin_name not in visited:
                visit(plugin_name)
                
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Set configuration for a plugin"""
        self.plugin_configs[plugin_name] = config
        
        # Apply to plugin if already loaded
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            import asyncio
            asyncio.create_task(plugin.configure(config))
            
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get plugin information"""
        plugin = self.get_plugin(plugin_name)
        return plugin.info if plugin else None
        
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins with their status"""
        plugin_list = []
        
        for plugin_name, plugin in self.plugins.items():
            plugin_list.append({
                "name": plugin_name,
                "version": plugin.info.version,
                "description": plugin.info.description,
                "author": plugin.info.author,
                "state": plugin.state.value,
                "dependencies": plugin.info.dependencies,
                "tags": plugin.info.tags
            })
            
        return plugin_list
        
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics"""
        
        state_counts = {}
        for plugin in self.plugins.values():
            state = plugin.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
            
        hook_counts = {hook_type.value: len(hooks) 
                      for hook_type, hooks in self.hooks.items()}
        
        return {
            "total_plugins": len(self.plugins),
            "plugin_states": state_counts,
            "hook_counts": hook_counts,
            "load_order": self.load_order
        }


# Import asyncio at module level to avoid issues
import asyncio
