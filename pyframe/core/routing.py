"""
Routing System

Handles URL routing for both server-side and client-side navigation,
with support for dynamic routes, middleware, and automatic API generation.
"""

import re
from typing import Dict, List, Any, Optional, Callable, Tuple, Type, Union
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from .component import Component


@dataclass
class Route:
    """Represents a single route in the application"""
    path: str
    handler: Callable
    methods: List[str]
    component: Optional[Type[Component]] = None
    middleware: List[Callable] = None
    name: Optional[str] = None
    
    def __post_init__(self):
        if self.middleware is None:
            self.middleware = []
            
        # Generate name if not provided
        if self.name is None:
            self.name = f"{'-'.join(self.methods).lower()}-{self.path.replace('/', '-').strip('-')}"
            
        # Compile path pattern for matching
        self._pattern = self._compile_path_pattern(self.path)
        
    def _compile_path_pattern(self, path: str) -> re.Pattern:
        """Compile a path pattern into a regex for matching"""
        # Convert path parameters to regex groups
        # /users/:id -> /users/(?P<id>[^/]+)
        # /users/:id/posts/:post_id -> /users/(?P<id>[^/]+)/posts/(?P<post_id>[^/]+)
        
        pattern = path
        
        # Handle path parameters (:param)
        pattern = re.sub(r':(\w+)', r'(?P<\1>[^/]+)', pattern)
        
        # Handle wildcard (*) 
        pattern = pattern.replace('*', '.*')
        
        # Escape dots and other regex special chars
        pattern = pattern.replace('.', r'\.')
        
        # Ensure exact match
        pattern = f'^{pattern}$'
        
        return re.compile(pattern)
        
    def matches(self, path: str, method: str) -> Tuple[bool, Dict[str, str]]:
        """Check if this route matches a given path and method"""
        if method not in self.methods:
            return False, {}
            
        match = self._pattern.match(path)
        if match:
            return True, match.groupdict()
        else:
            return False, {}


class Router:
    """
    Main routing system for PyFrame applications.
    
    Handles both server-side routing and client-side navigation,
    with support for nested routes, middleware, and automatic API generation.
    """
    
    def __init__(self):
        self._routes: List[Route] = []
        self._middleware: List[Callable] = []
        self._base_path = ""
        
    def add_route(self, route: Route) -> None:
        """Add a route to the router"""
        self._routes.append(route)
        
    def route(self, path: str, methods: List[str] = None, 
              component: Type[Component] = None, name: str = None):
        """Decorator to register a route"""
        def decorator(handler):
            route = Route(
                path=self._base_path + path,
                handler=handler,
                methods=methods or ["GET"],
                component=component,
                name=name
            )
            self.add_route(route)
            return handler
        return decorator
        
    def get(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a GET route"""
        return self.route(path, ["GET"], component, name)
        
    def post(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a POST route"""
        return self.route(path, ["POST"], component, name)
        
    def put(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a PUT route"""
        return self.route(path, ["PUT"], component, name)
        
    def delete(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a DELETE route"""
        return self.route(path, ["DELETE"], component, name)
        
    def patch(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a PATCH route"""
        return self.route(path, ["PATCH"], component, name)
        
    def add_middleware(self, middleware: Callable) -> None:
        """Add global middleware"""
        self._middleware.append(middleware)
        
    def group(self, prefix: str):
        """Create a route group with shared prefix"""
        return RouteGroup(self, prefix)
        
    def match(self, path: str, method: str) -> Tuple[Optional[Route], Dict[str, str]]:
        """Find the first route that matches the given path and method"""
        for route in self._routes:
            matches, params = route.matches(path, method)
            if matches:
                return route, params
        return None, {}
        
    def reverse(self, name: str, **params) -> str:
        """Generate URL for a named route with parameters"""
        for route in self._routes:
            if route.name == name:
                url = route.path
                for param, value in params.items():
                    url = url.replace(f':{param}', str(value))
                return url
        raise ValueError(f"No route found with name '{name}'")
        
    def get_routes(self) -> List[Route]:
        """Get all registered routes"""
        return self._routes.copy()
        
    def generate_client_routes(self) -> str:
        """Generate JavaScript routing code for client-side navigation"""
        routes_data = []
        
        for route in self._routes:
            if route.component:  # Only include component routes for client-side
                routes_data.append({
                    "path": route.path,
                    "component": route.component.__name__,
                    "name": route.name
                })
                
        return f"""
// Auto-generated client-side routes
window.PyFrameRoutes = {routes_data};

class PyFrameRouter {{
    constructor() {{
        this.routes = window.PyFrameRoutes;
        this.currentRoute = null;
        this.setupEventListeners();
    }}
    
    setupEventListeners() {{
        // Handle popstate for back/forward navigation
        window.addEventListener('popstate', (e) => {{
            this.navigate(window.location.pathname, false);
        }});
        
        // Handle link clicks
        document.addEventListener('click', (e) => {{
            if (e.target.tagName === 'A' && e.target.href && 
                e.target.href.startsWith(window.location.origin)) {{
                e.preventDefault();
                const path = new URL(e.target.href).pathname;
                this.navigate(path);
            }}
        }});
    }}
    
    navigate(path, pushState = true) {{
        const route = this.matchRoute(path);
        if (route) {{
            if (pushState) {{
                history.pushState(null, '', path);
            }}
            this.currentRoute = route;
            this.renderRoute(route, path);
        }}
    }}
    
    matchRoute(path) {{
        for (const route of this.routes) {{
            const pattern = this.compilePattern(route.path);
            if (pattern.test(path)) {{
                return route;
            }}
        }}
        return null;
    }}
    
    compilePattern(path) {{
        let pattern = path.replace(/:(\w+)/g, '([^/]+)');
        pattern = pattern.replace(/\*/g, '.*');
        return new RegExp(`^${{pattern}}$`);
    }}
    
    renderRoute(route, path) {{
        // Extract path parameters
        const pattern = this.compilePattern(route.path);
        const match = pattern.exec(path);
        const params = {{}};
        
        if (match) {{
            const paramNames = route.path.match(/:(\w+)/g);
            if (paramNames) {{
                paramNames.forEach((param, index) => {{
                    const paramName = param.slice(1);
                    params[paramName] = match[index + 1];
                }});
            }}
        }}
        
        // Render component
        const ComponentClass = window[route.component];
        if (ComponentClass) {{
            const component = new ComponentClass(params);
            const appElement = document.getElementById('app');
            if (appElement) {{
                appElement.innerHTML = component.render();
            }}
        }}
    }}
}}

// Initialize router
window.PyFrameRouterInstance = new PyFrameRouter();
"""


class RouteGroup:
    """A group of routes with shared prefix and middleware"""
    
    def __init__(self, router: Router, prefix: str):
        self.router = router
        self.prefix = prefix.rstrip('/')
        self._middleware: List[Callable] = []
        
    def route(self, path: str, methods: List[str] = None, 
              component: Type[Component] = None, name: str = None):
        """Register a route within this group"""
        def decorator(handler):
            full_path = self.prefix + path
            route = Route(
                path=full_path,
                handler=handler,
                methods=methods or ["GET"],
                component=component,
                middleware=self._middleware.copy(),
                name=name
            )
            self.router.add_route(route)
            return handler
        return decorator
        
    def get(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a GET route in this group"""
        return self.route(path, ["GET"], component, name)
        
    def post(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a POST route in this group"""
        return self.route(path, ["POST"], component, name)
        
    def put(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a PUT route in this group"""
        return self.route(path, ["PUT"], component, name)
        
    def delete(self, path: str, component: Type[Component] = None, name: str = None):
        """Register a DELETE route in this group"""
        return self.route(path, ["DELETE"], component, name)
        
    def middleware(self, middleware: Callable):
        """Add middleware to this route group"""
        self._middleware.append(middleware)
        return middleware


# Utility functions for common routing patterns

def resource_routes(router: Router, name: str, controller_class: Type,
                   prefix: str = None) -> None:
    """
    Register RESTful resource routes.
    
    Creates standard CRUD routes:
    GET /resource -> index
    GET /resource/:id -> show  
    POST /resource -> create
    PUT /resource/:id -> update
    DELETE /resource/:id -> destroy
    """
    prefix = prefix or f"/{name}"
    controller = controller_class()
    
    if hasattr(controller, 'index'):
        router.add_route(Route(prefix, controller.index, ["GET"], name=f"{name}.index"))
        
    if hasattr(controller, 'show'):
        router.add_route(Route(f"{prefix}/:id", controller.show, ["GET"], name=f"{name}.show"))
        
    if hasattr(controller, 'create'):
        router.add_route(Route(prefix, controller.create, ["POST"], name=f"{name}.create"))
        
    if hasattr(controller, 'update'):
        router.add_route(Route(f"{prefix}/:id", controller.update, ["PUT"], name=f"{name}.update"))
        
    if hasattr(controller, 'destroy'):
        router.add_route(Route(f"{prefix}/:id", controller.destroy, ["DELETE"], name=f"{name}.destroy"))


def api_routes(router: Router, version: str = "v1") -> RouteGroup:
    """Create an API route group with versioning"""
    return router.group(f"/api/{version}")


# Example usage demonstrating the routing system

class HomePageComponent(Component):
    """Example home page component"""
    
    def render(self) -> str:
        return """
        <div>
            <h1>Welcome to PyFrame</h1>
            <nav>
                <a href="/about">About</a>
                <a href="/users">Users</a>
                <a href="/dashboard">Dashboard</a>
            </nav>
        </div>
        """


class UserProfileComponent(Component):
    """Example user profile component"""
    
    def render(self) -> str:
        user_id = self.props.get("id", "unknown")
        return f"""
        <div>
            <h1>User Profile: {user_id}</h1>
            <p>User details would go here...</p>
            <a href="/users">Back to Users</a>
        </div>
        """


# Example of how routes would be registered
def setup_example_routes(router: Router):
    """Set up example routes to demonstrate the system"""
    
    # Component routes
    router.add_route(Route("/", lambda ctx: "home", ["GET"], HomePageComponent, name="home"))
    router.add_route(Route("/users/:id", lambda ctx: "user", ["GET"], UserProfileComponent, name="user.profile"))
    
    # API routes
    api_group = router.group("/api/v1")
    
    @api_group.get("/users")
    async def get_users(context):
        return {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}
        
    @api_group.get("/users/:id")  
    async def get_user(context):
        user_id = context.path_params["id"]
        return {"user": {"id": user_id, "name": f"User {user_id}"}}
        
    @api_group.post("/users")
    async def create_user(context):
        # User creation logic here
        return {"message": "User created", "user": {"id": 3, "name": "New User"}}
