"""
PyFrame Application Framework

The main application class that orchestrates all framework components,
handles routing, server-side rendering, and coordinates plugins.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from pathlib import Path

from .component import Component
from .routing import Router, Route
from ..server.context import RequestContext, ClientContext
from ..plugins.plugin import Plugin, PluginManager
from ..compiler.transpiler import PythonToJSTranspiler
from ..data.models import ModelRegistry


@dataclass
class PyFrameConfig:
    """Configuration for PyFrame application"""
    debug: bool = True
    hot_reload: bool = True
    auto_reload: bool = True
    
    # Server settings
    host: str = "localhost"
    port: int = 3000
    
    # Rendering settings
    ssr_enabled: bool = True
    hydration_strategy: str = "partial"  # full, partial, lazy
    
    # Build settings
    minify_js: bool = False
    source_maps: bool = True
    
    # Data layer settings
    database_url: str = "sqlite:///app.db"
    auto_migrate: bool = True
    
    # Security settings
    csrf_protection: bool = True
    secure_cookies: bool = False
    
    # Plugin settings
    plugin_directories: List[str] = field(default_factory=lambda: ["plugins"])


class PyFrameApp:
    """
    Main PyFrame application class.
    
    Coordinates all framework components including routing, rendering,
    state management, plugins, and the development server.
    """
    
    def __init__(self, config: PyFrameConfig = None):
        self.config = config or PyFrameConfig()
        
        # Core components
        self.router = Router()
        self.plugin_manager = PluginManager()
        self.transpiler = PythonToJSTranspiler()
        self.model_registry = ModelRegistry()
        
        # Application state
        self._middleware: List[Callable] = []
        self._error_handlers: Dict[int, Callable] = {}
        self._template_globals: Dict[str, Any] = {}
        self._static_files: Dict[str, str] = {}
        
        # Development server state
        self._dev_server = None
        self._is_running = False
        
        # Initialize plugins
        self._load_plugins()
        
    def route(self, path: str, methods: List[str] = None, 
              component: Type[Component] = None):
        """
        Decorator to register routes.
        
        Can be used for both API endpoints and component routes.
        """
        def decorator(handler):
            route = Route(
                path=path,
                handler=handler,
                methods=methods or ["GET"],
                component=component
            )
            self.router.add_route(route)
            return handler
        return decorator
        
    def component_route(self, path: str, methods: List[str] = None):
        """Decorator specifically for component-based routes"""
        def decorator(component_class):
            route = Route(
                path=path,
                handler=self._create_component_handler(component_class),
                methods=methods or ["GET"],
                component=component_class
            )
            self.router.add_route(route)
            return component_class
        return decorator
        
    def _create_component_handler(self, component_class: Type[Component]):
        """Create a handler function for a component route"""
        async def handler(context: RequestContext):
            # Extract props from request
            props = {**context.query_params, **context.path_params}
            
            # Create component instance
            component = component_class(props)
            
            # Server-side render
            if self.config.ssr_enabled:
                html = await self._render_component_ssr(component, context)
                return html
            else:
                # Return basic HTML with client-side rendering
                return await self._render_spa_shell(component, context)
                
        return handler
        
    async def _render_component_ssr(self, component: Component, 
                                  context: RequestContext) -> str:
        """Render component on server-side"""
        # Render component to HTML
        component_html = component.render()
        
        # Generate client-side JavaScript
        transpilation_result = self.transpiler.transpile_component(component)
        client_js = transpilation_result.js_code
        
        # Create hydration data
        hydration_data = {
            "component": component.to_dict(),
            "context": context.to_dict()
        }
        
        # Build complete HTML page
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{context.get_title()}</title>
            <script src="/static/pyframe-runtime.js"></script>
            {self._generate_adaptive_meta_tags(context.client_context)}
        </head>
        <body>
            <div id="app">{component_html}</div>
            <script>
                window.__PYFRAME_HYDRATION_DATA__ = {json.dumps(hydration_data)};
                {client_js}
                PyFrame.hydrate(document.getElementById('app'), window.__PYFRAME_HYDRATION_DATA__);
            </script>
        </body>
        </html>
        """
        
        return html
        
    async def _render_spa_shell(self, component: Component, 
                              context: RequestContext) -> str:
        """Render SPA shell for client-side rendering"""
        client_js = self.transpiler.transpile_component(component)
        
        initial_data = {
            "component": component.to_dict(),
            "context": context.to_dict()
        }
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{context.get_title()}</title>
            <script src="/static/pyframe-runtime.js"></script>
            {self._generate_adaptive_meta_tags(context.client_context)}
        </head>
        <body>
            <div id="app">Loading...</div>
            <script>
                window.__PYFRAME_INITIAL_DATA__ = {json.dumps(initial_data)};
                {client_js}
                PyFrame.render(document.getElementById('app'), window.__PYFRAME_INITIAL_DATA__);
            </script>
        </body>
        </html>
        """
        
        return html
        
    def _generate_adaptive_meta_tags(self, client_context: ClientContext) -> str:
        """Generate context-aware meta tags"""
        meta_tags = []
        
        # Dark mode preference
        if client_context.prefers_dark_mode:
            meta_tags.append('<meta name="color-scheme" content="dark light">')
        
        # Reduced motion preference  
        if client_context.prefers_reduced_motion:
            meta_tags.append('<meta name="prefers-reduced-motion" content="reduce">')
            
        # Device-specific optimizations
        if client_context.device_type == "mobile":
            meta_tags.append('<meta name="format-detection" content="telephone=no">')
            
        # Network-aware loading
        if client_context.connection_type in ["slow-2g", "2g"]:
            meta_tags.append('<meta name="resource-loading" content="conservative">')
            
        return "\n".join(meta_tags)
        
    def middleware(self, func: Callable):
        """Decorator to register middleware"""
        self._middleware.append(func)
        return func
        
    def error_handler(self, status_code: int):
        """Decorator to register error handlers"""
        def decorator(func):
            self._error_handlers[status_code] = func
            return func
        return decorator
        
    def add_static_files(self, url_path: str, directory: str):
        """Add static file serving"""
        self._static_files[url_path] = directory
        
    def register_plugin(self, plugin: Plugin):
        """Register a plugin with the application"""
        self.plugin_manager.register(plugin)
        # Plugin initialization will be handled in initialize_all()
        
    def _load_plugins(self):
        """Load plugins from configured directories"""
        for plugin_dir in self.config.plugin_directories:
            if os.path.exists(plugin_dir):
                self.plugin_manager.load_from_directory(plugin_dir)
                
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming HTTP request.
        
        This method processes the request through middleware, routing,
        and rendering pipeline.
        """
        # Create request context
        context = RequestContext.from_request(request_data)
        
        try:
            # Apply middleware
            for middleware in self._middleware:
                context = await middleware(context)
                if context.response:
                    return context.response
                    
            # Route the request
            route, params = self.router.match(context.path, context.method)
            if route:
                context.path_params = params
                response = await route.handler(context)
                
                if isinstance(response, str):
                    return {
                        "status": 200,
                        "headers": {"Content-Type": "text/html"},
                        "body": response
                    }
                else:
                    return response
            else:
                # 404 Not Found
                if 404 in self._error_handlers:
                    response = await self._error_handlers[404](context)
                    return response
                else:
                    return {
                        "status": 404,
                        "headers": {"Content-Type": "text/html"},
                        "body": "<h1>404 - Page Not Found</h1>"
                    }
                    
        except Exception as e:
            # Handle errors
            if 500 in self._error_handlers:
                response = await self._error_handlers[500](context, e)
                return response
            else:
                error_html = f"<h1>500 - Internal Server Error</h1><pre>{str(e)}</pre>"
                return {
                    "status": 500,
                    "headers": {"Content-Type": "text/html"},
                    "body": error_html
                }
                
    async def start_dev_server(self):
        """Start the development server with hot reload"""
        from ..server.simple_server import SimpleDevServer

        # Initialize plugins
        await self.plugin_manager.initialize_all(self)

        self._dev_server = SimpleDevServer(self, self.config)
        await self._dev_server.start()
        self._is_running = True
        
        print(f"PyFrame dev server running at http://{self.config.host}:{self.config.port}")
        
        if self.config.hot_reload:
            print("Hot reload enabled")
            
    async def stop_dev_server(self):
        """Stop the development server"""
        if self._dev_server:
            await self._dev_server.stop()
            self._is_running = False
            
    def run(self):
        """Run the application (development mode)"""
        try:
            asyncio.run(self.start_dev_server())
        except KeyboardInterrupt:
            print("\nShutting down PyFrame dev server...")
            
    def build_for_production(self, output_dir: str = "dist"):
        """Build the application for production deployment"""
        from ..build.builder import ProductionBuilder
        
        builder = ProductionBuilder(self, self.config)
        builder.build(output_dir)
        
    def create_wsgi_app(self):
        """Create a WSGI application for deployment"""
        from ..deployment.wsgi import create_wsgi_app
        return create_wsgi_app(self)
        
    def create_asgi_app(self):
        """Create an ASGI application for deployment"""  
        from ..deployment.asgi import create_asgi_app
        return create_asgi_app(self)


# Convenience function for creating apps
def create_app(config: PyFrameConfig = None) -> PyFrameApp:
    """Create a new PyFrame application"""
    return PyFrameApp(config)
