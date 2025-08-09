# Plugin Development

PyFrame's plugin system allows you to extend the framework with reusable components. This guide covers creating, distributing, and using PyFrame plugins.

## 🔌 Plugin Basics

### What is a Plugin?

A PyFrame plugin is a Python package that extends framework functionality through:
- **Middleware**: Request/response processing
- **Commands**: CLI extensions
- **Components**: Reusable UI components
- **Models**: Data layer extensions
- **Services**: Background services and utilities

### Plugin Structure

```
my_pyframe_plugin/
├── __init__.py
├── plugin.py          # Main plugin class
├── middleware.py       # Request middleware
├── components/         # UI components
│   ├── __init__.py
│   └── button.py
├── models/            # Data models
│   ├── __init__.py
│   └── analytics.py
├── commands/          # CLI commands
│   ├── __init__.py
│   └── migrate.py
├── static/           # Static assets
│   ├── css/
│   └── js/
└── templates/        # Template files
    └── analytics.html
```

## 🏗️ Creating Your First Plugin

### Basic Plugin Class

```python
# plugin.py
from pyframe.plugins import Plugin
from pyframe.hooks import hook

class MyPlugin(Plugin):
    """Example plugin demonstrating core features"""
    
    name = "my-plugin"
    version = "1.0.0"
    description = "An example PyFrame plugin"
    
    def __init__(self, **config):
        super().__init__(**config)
        self.api_key = config.get('api_key')
        self.enabled = config.get('enabled', True)
    
    async def initialize(self, app):
        """Initialize plugin when app starts"""
        if not self.enabled:
            return
        
        print(f"Initializing {self.name} v{self.version}")
        
        # Register middleware
        app.middleware.append(self.request_middleware)
        
        # Register hooks
        app.hooks.register('user_created', self.on_user_created)
        app.hooks.register('request_completed', self.on_request_completed)
        
        # Register CLI commands
        self.register_commands(app)
        
        # Register static files
        app.add_static_path('/plugin-static/', self.get_static_path())
    
    async def request_middleware(self, context, call_next):
        """Middleware to process requests"""
        # Before request
        context.plugin_start_time = time.time()
        
        # Process request
        response = await call_next(context)
        
        # After request
        duration = time.time() - context.plugin_start_time
        print(f"Request processed in {duration:.3f}s")
        
        return response
    
    async def on_user_created(self, user):
        """Hook called when user is created"""
        print(f"New user created: {user.name}")
        await self.track_event('user_signup', {'user_id': user.id})
    
    async def on_request_completed(self, context, response):
        """Hook called after request completion"""
        await self.track_event('page_view', {
            'path': context.path,
            'status': response.get('status', 200)
        })
    
    async def track_event(self, event_type, data):
        """Track analytics events"""
        if self.api_key:
            # Send to analytics service
            pass
    
    def register_commands(self, app):
        """Register CLI commands"""
        from .commands import AnalyticsCommand
        app.cli.add_command(AnalyticsCommand(self))
    
    def get_static_path(self):
        """Get path to static files"""
        import os
        return os.path.join(os.path.dirname(__file__), 'static')
```

### Plugin Configuration

```python
# __init__.py
from .plugin import MyPlugin

def create_plugin(**config):
    """Plugin factory function"""
    return MyPlugin(**config)

# Plugin metadata
__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "An example PyFrame plugin"
```

## 🛠️ Plugin Types and Examples

### 1. Authentication Plugin

```python
from pyframe.plugins import Plugin
from pyframe.auth import AuthBackend
import jwt

class JWTAuthPlugin(Plugin):
    """JWT Authentication plugin"""
    
    name = "jwt-auth"
    
    def __init__(self, **config):
        super().__init__(**config)
        self.secret_key = config['secret_key']
        self.algorithm = config.get('algorithm', 'HS256')
        self.token_header = config.get('token_header', 'Authorization')
    
    async def initialize(self, app):
        # Register auth backend
        app.auth.add_backend(JWTBackend(self))
        
        # Add auth middleware
        app.middleware.insert(0, self.auth_middleware)
    
    async def auth_middleware(self, context, call_next):
        """Extract and validate JWT token"""
        token = self.extract_token(context)
        
        if token:
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                user = await self.get_user(payload['user_id'])
                context.user = user
            except jwt.InvalidTokenError:
                context.user = None
        else:
            context.user = None
        
        return await call_next(context)
    
    def extract_token(self, context):
        """Extract token from request headers"""
        auth_header = context.headers.get(self.token_header, '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
    
    async def get_user(self, user_id):
        """Get user by ID"""
        from myapp.models import User
        return await User.get(id=user_id)
    
    def generate_token(self, user):
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

class JWTBackend(AuthBackend):
    def __init__(self, plugin):
        self.plugin = plugin
    
    async def authenticate(self, username, password):
        """Authenticate user and return token"""
        user = await self.verify_credentials(username, password)
        if user:
            token = self.plugin.generate_token(user)
            return {'user': user, 'token': token}
        return None
```

### 2. Caching Plugin

```python
import redis
import pickle
from pyframe.plugins import Plugin

class RedisCachePlugin(Plugin):
    """Redis caching plugin"""
    
    name = "redis-cache"
    
    def __init__(self, **config):
        super().__init__(**config)
        self.redis_url = config['redis_url']
        self.default_timeout = config.get('default_timeout', 300)
        self.key_prefix = config.get('key_prefix', 'pyframe:')
    
    async def initialize(self, app):
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url)
        
        # Add cache to app
        app.cache = self
        
        # Register middleware for automatic caching
        if self.config.get('auto_cache', False):
            app.middleware.append(self.cache_middleware)
    
    async def cache_middleware(self, context, call_next):
        """Automatic caching middleware"""
        if context.method == 'GET':
            cache_key = self.generate_cache_key(context)
            cached_response = await self.get(cache_key)
            
            if cached_response:
                return cached_response
            
            response = await call_next(context)
            
            if response.get('status') == 200:
                await self.set(cache_key, response, timeout=self.default_timeout)
            
            return response
        
        return await call_next(context)
    
    def generate_cache_key(self, context):
        """Generate cache key from request"""
        key_parts = [context.path]
        if context.query_params:
            query_string = '&'.join(f"{k}={v}" for k, v in sorted(context.query_params.items()))
            key_parts.append(query_string)
        
        cache_key = ':'.join(key_parts)
        return f"{self.key_prefix}page:{cache_key}"
    
    async def get(self, key):
        """Get value from cache"""
        try:
            data = self.redis.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    async def set(self, key, value, timeout=None):
        """Set value in cache"""
        try:
            timeout = timeout or self.default_timeout
            data = pickle.dumps(value)
            self.redis.setex(key, timeout, data)
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def delete(self, key):
        """Delete value from cache"""
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    async def clear(self, pattern=None):
        """Clear cache entries"""
        try:
            if pattern:
                keys = self.redis.keys(f"{self.key_prefix}{pattern}")
                if keys:
                    self.redis.delete(*keys)
            else:
                keys = self.redis.keys(f"{self.key_prefix}*")
                if keys:
                    self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache clear error: {e}")
```

### 3. Database Plugin

```python
from pyframe.plugins import Plugin
from pyframe.database import DatabaseBackend
import asyncpg

class PostgreSQLPlugin(Plugin):
    """PostgreSQL database plugin"""
    
    name = "postgresql"
    
    def __init__(self, **config):
        super().__init__(**config)
        self.database_url = config['database_url']
        self.pool_size = config.get('pool_size', 20)
        self.pool = None
    
    async def initialize(self, app):
        # Create connection pool
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=self.pool_size
        )
        
        # Register database backend
        app.database.add_backend('postgresql', PostgreSQLBackend(self.pool))
        
        # Register cleanup hook
        app.hooks.register('app_shutdown', self.cleanup)
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.pool:
            await self.pool.close()

class PostgreSQLBackend(DatabaseBackend):
    def __init__(self, pool):
        self.pool = pool
    
    async def execute(self, query, params=None):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *(params or []))
    
    async def fetch(self, query, params=None):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *(params or []))
    
    async def fetchrow(self, query, params=None):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *(params or []))
```

### 4. UI Component Plugin

```python
from pyframe.plugins import Plugin
from pyframe import Component

class UIComponentsPlugin(Plugin):
    """UI components plugin"""
    
    name = "ui-components"
    
    async def initialize(self, app):
        # Register components globally
        app.register_component('ui-button', UIButton)
        app.register_component('ui-modal', UIModal)
        app.register_component('ui-form', UIForm)
        
        # Add static assets
        app.add_static_path('/ui-components/', self.get_static_path())

class UIButton(Component):
    """Reusable button component"""
    
    def render(self):
        text = self.props.get('text', 'Button')
        variant = self.props.get('variant', 'primary')
        size = self.props.get('size', 'medium')
        disabled = self.props.get('disabled', False)
        onclick = self.props.get('onclick', '')
        
        disabled_attr = 'disabled' if disabled else ''
        css_classes = f"ui-button ui-button--{variant} ui-button--{size}"
        
        return f'''
        <button class="{css_classes}" 
                onclick="{onclick}" 
                {disabled_attr}>
            {text}
        </button>
        '''
    
    def get_styles(self):
        return '''
        .ui-button {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 0.25rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .ui-button--primary {
            background: #3b82f6;
            color: white;
        }
        
        .ui-button--primary:hover {
            background: #2563eb;
        }
        
        .ui-button--secondary {
            background: #6b7280;
            color: white;
        }
        
        .ui-button--small {
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
        }
        
        .ui-button--large {
            padding: 0.75rem 1.5rem;
            font-size: 1.125rem;
        }
        
        .ui-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        '''

class UIModal(Component):
    """Reusable modal component"""
    
    def render(self):
        title = self.props.get('title', 'Modal')
        content = self.props.get('content', '')
        show = self.props.get('show', False)
        on_close = self.props.get('on_close', '')
        
        display_style = 'display: flex;' if show else 'display: none;'
        
        return f'''
        <div class="ui-modal-overlay" style="{display_style}" onclick="{on_close}">
            <div class="ui-modal" onclick="event.stopPropagation()">
                <div class="ui-modal-header">
                    <h3>{title}</h3>
                    <button class="ui-modal-close" onclick="{on_close}">&times;</button>
                </div>
                <div class="ui-modal-content">
                    {content}
                </div>
            </div>
        </div>
        '''
```

## 📋 Plugin Hooks and Events

### Available Hooks

```python
# Application lifecycle
app.hooks.register('app_startup', callback)
app.hooks.register('app_shutdown', callback)

# Request lifecycle
app.hooks.register('request_started', callback)
app.hooks.register('request_completed', callback)
app.hooks.register('response_sent', callback)

# User events
app.hooks.register('user_created', callback)
app.hooks.register('user_logged_in', callback)
app.hooks.register('user_logged_out', callback)

# Database events
app.hooks.register('model_created', callback)
app.hooks.register('model_updated', callback)
app.hooks.register('model_deleted', callback)

# Error handling
app.hooks.register('error_occurred', callback)
app.hooks.register('exception_caught', callback)
```

### Creating Custom Hooks

```python
class CustomPlugin(Plugin):
    async def initialize(self, app):
        # Register custom hook
        app.hooks.register('payment_processed', self.on_payment)
        
        # Trigger custom hook from your code
        await app.hooks.trigger('payment_processed', payment_data)
    
    async def on_payment(self, payment_data):
        """Handle payment processed event"""
        await self.send_receipt_email(payment_data['user_email'])
        await self.update_analytics(payment_data)
```

## 📦 Plugin Distribution

### Package Structure

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="pyframe-analytics-plugin",
    version="1.0.0",
    description="Analytics plugin for PyFrame",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "pyframe-web>=0.1.0",
        "aiohttp>=3.8.0",
    ],
    entry_points={
        "pyframe.plugins": [
            "analytics = pyframe_analytics:create_plugin",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8+",
    ],
    include_package_data=True,
    package_data={
        "pyframe_analytics": ["static/*", "templates/*"],
    },
)
```

### Plugin Registry

```python
# pyproject.toml
[project.entry-points."pyframe.plugins"]
analytics = "pyframe_analytics:create_plugin"
auth = "pyframe_auth:create_plugin"
cache = "pyframe_cache:create_plugin"
```

## 🚀 Using Plugins

### Installing Plugins

```bash
# Install from PyPI
pip install pyframe-analytics-plugin

# Install from source
pip install git+https://github.com/user/pyframe-plugin.git
```

### Loading Plugins

```python
from pyframe import PyFrameApp
from pyframe_analytics import create_plugin as create_analytics_plugin

app = PyFrameApp()

# Method 1: Direct instantiation
analytics_plugin = create_analytics_plugin(
    api_key='your-analytics-key',
    enabled=True
)
app.use_plugin(analytics_plugin)

# Method 2: Plugin discovery
app.discover_plugins()  # Auto-loads installed plugins

# Method 3: Configuration-based loading
app.load_plugins({
    'analytics': {
        'api_key': 'your-key',
        'enabled': True
    },
    'cache': {
        'redis_url': 'redis://localhost:6379',
        'default_timeout': 300
    }
})
```

### Plugin Configuration

```python
# config.py
PLUGINS = {
    'analytics': {
        'api_key': os.getenv('ANALYTICS_API_KEY'),
        'enabled': True,
        'batch_size': 50
    },
    'auth': {
        'secret_key': os.getenv('JWT_SECRET'),
        'algorithm': 'HS256',
        'token_expiry': 3600
    },
    'cache': {
        'backend': 'redis',
        'redis_url': os.getenv('REDIS_URL'),
        'default_timeout': 300
    }
}

# main.py
app = PyFrameApp()
app.load_plugins(PLUGINS)
```

## 🧪 Testing Plugins

### Plugin Test Setup

```python
import pytest
from pyframe import PyFrameApp
from your_plugin import YourPlugin

@pytest.fixture
async def app():
    """Create test app with plugin"""
    app = PyFrameApp(debug=True)
    plugin = YourPlugin(test_mode=True)
    app.use_plugin(plugin)
    await app.initialize()
    return app

@pytest.fixture
async def client(app):
    """Create test client"""
    from pyframe.testing import TestClient
    return TestClient(app)

async def test_plugin_middleware(client):
    """Test plugin middleware"""
    response = await client.get('/')
    assert response.status == 200
    assert 'X-Plugin-Header' in response.headers

async def test_plugin_hook(app):
    """Test plugin hooks"""
    # Trigger hook and verify behavior
    await app.hooks.trigger('test_event', {'data': 'test'})
    
    # Assert expected side effects
    assert app.plugin.event_received
```

### Mocking External Services

```python
import pytest
from unittest.mock import AsyncMock, patch

async def test_analytics_plugin_with_mock():
    """Test analytics plugin with mocked API"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        
        plugin = AnalyticsPlugin(api_key='test-key')
        await plugin.track_event('test_event', {'user_id': 123})
        
        mock_post.assert_called_once()
```

## 📚 Best Practices

### 1. Plugin Design
```python
# Good: Configurable and optional
class GoodPlugin(Plugin):
    def __init__(self, **config):
        self.enabled = config.get('enabled', True)
        self.api_key = config.get('api_key')
        
    async def initialize(self, app):
        if not self.enabled:
            return
        
        if not self.api_key:
            raise ValueError("api_key is required")

# Bad: Hard-coded behavior
class BadPlugin(Plugin):
    def __init__(self):
        self.api_key = "hardcoded-key"  # Bad!
```

### 2. Error Handling
```python
class RobustPlugin(Plugin):
    async def request_middleware(self, context, call_next):
        try:
            # Plugin logic here
            return await call_next(context)
        except Exception as e:
            # Log error but don't break the request
            self.logger.error(f"Plugin error: {e}")
            return await call_next(context)
```

### 3. Resource Cleanup
```python
class CleanPlugin(Plugin):
    async def initialize(self, app):
        self.background_task = asyncio.create_task(self.background_worker())
        app.hooks.register('app_shutdown', self.cleanup)
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        if hasattr(self, 'background_task'):
            self.background_task.cancel()
        
        if hasattr(self, 'connection_pool'):
            await self.connection_pool.close()
```

### 4. Documentation
```python
class WellDocumentedPlugin(Plugin):
    """
    Analytics tracking plugin for PyFrame applications.
    
    This plugin provides automatic page view tracking, custom event tracking,
    and user behavior analytics.
    
    Configuration:
        api_key (str): Required. Your analytics API key.
        enabled (bool): Whether to enable tracking. Default: True.
        batch_size (int): Number of events to batch. Default: 50.
        flush_interval (int): Seconds between flushes. Default: 30.
    
    Example:
        plugin = AnalyticsPlugin(
            api_key='your-key',
            batch_size=100
        )
        app.use_plugin(plugin)
    """
    pass
```

Plugins are the key to extending PyFrame's capabilities. Start simple, follow best practices, and build amazing extensions! 🔌
