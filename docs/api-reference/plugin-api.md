# Plugin API Reference

Complete reference for PyFrame's plugin system API.

## Base Plugin Class

### `Plugin`

Base class for all PyFrame plugins.

```python
from pyframe.plugins import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom plugin"
    
    def __init__(self, **config):
        super().__init__(**config)
        self.enabled = config.get('enabled', True)
    
    async def initialize(self, app):
        # Plugin initialization logic
        pass
```

#### Class Attributes

##### `name: str`
Unique plugin identifier.

##### `version: str`
Plugin version string.

##### `description: str`
Human-readable plugin description.

#### Methods

##### `__init__(self, **config)`
Initialize plugin with configuration.

**Parameters:**
- `**config` - Plugin configuration options

##### `async initialize(self, app)`
Initialize plugin when application starts.

**Parameters:**
- `app: PyFrameApp` - Application instance

**Example:**
```python
async def initialize(self, app):
    # Register middleware
    app.middleware.append(self.my_middleware)
    
    # Register hooks
    app.hooks.register('user_created', self.on_user_created)
    
    # Add static files
    app.add_static_path('/plugin-static/', self.get_static_path())
```

##### `get_static_path(self) -> str`
Get path to plugin's static files.

**Returns:**
- `str` - Absolute path to static files directory

##### `get_template_path(self) -> str`
Get path to plugin's template files.

**Returns:**
- `str` - Absolute path to templates directory

---

## Plugin Manager

### `PluginManager`

Manages plugin loading, initialization, and lifecycle.

```python
from pyframe.plugins import PluginManager

manager = PluginManager()
await manager.load_plugin('my-plugin', config={'enabled': True})
```

#### Methods

##### `async load_plugin(self, plugin_name, config=None)`
Load and initialize a plugin.

**Parameters:**
- `plugin_name: str` - Name of plugin to load
- `config: dict` - Plugin configuration

**Returns:**
- `Plugin` - Loaded plugin instance

##### `async unload_plugin(self, plugin_name)`
Unload a plugin.

**Parameters:**
- `plugin_name: str` - Name of plugin to unload

##### `get_plugin(self, plugin_name) -> Plugin`
Get loaded plugin by name.

**Parameters:**
- `plugin_name: str` - Plugin name

**Returns:**
- `Plugin` - Plugin instance or None

##### `list_plugins(self) -> List[Plugin]`
Get list of all loaded plugins.

**Returns:**
- `List[Plugin]` - List of plugin instances

##### `discover_plugins(self) -> List[str]`
Discover available plugins from entry points.

**Returns:**
- `List[str]` - List of available plugin names

---

## Hook System

### `HookRegistry`

Manages application hooks and events.

```python
from pyframe.hooks import HookRegistry

hooks = HookRegistry()
hooks.register('user_created', callback_function)
await hooks.trigger('user_created', user_data)
```

#### Methods

##### `register(self, hook_name, callback)`
Register a callback for a hook.

**Parameters:**
- `hook_name: str` - Name of hook
- `callback: callable` - Callback function

**Example:**
```python
async def on_user_created(user):
    print(f"User created: {user.name}")

hooks.register('user_created', on_user_created)
```

##### `unregister(self, hook_name, callback)`
Unregister a callback from a hook.

**Parameters:**
- `hook_name: str` - Hook name
- `callback: callable` - Callback to remove

##### `async trigger(self, hook_name, *args, **kwargs)`
Trigger all callbacks for a hook.

**Parameters:**
- `hook_name: str` - Hook name
- `*args, **kwargs` - Arguments to pass to callbacks

##### `list_hooks(self) -> List[str]`
Get list of registered hook names.

**Returns:**
- `List[str]` - Hook names

##### `get_callbacks(self, hook_name) -> List[callable]`
Get callbacks for a specific hook.

**Parameters:**
- `hook_name: str` - Hook name

**Returns:**
- `List[callable]` - Registered callbacks

---

## Built-in Hooks

### Application Lifecycle

#### `app_startup`
Triggered when application starts.

```python
async def on_startup():
    print("Application starting...")

app.hooks.register('app_startup', on_startup)
```

#### `app_shutdown`
Triggered when application shuts down.

```python
async def on_shutdown():
    print("Application shutting down...")

app.hooks.register('app_shutdown', on_shutdown)
```

### Request Lifecycle

#### `request_started`
Triggered when request processing begins.

**Callback Signature:**
```python
async def on_request_started(context):
    print(f"Request started: {context.path}")
```

#### `request_completed`
Triggered when request processing completes.

**Callback Signature:**
```python
async def on_request_completed(context, response):
    print(f"Request completed: {response.get('status', 200)}")
```

#### `response_sent`
Triggered after response is sent to client.

**Callback Signature:**
```python
async def on_response_sent(context, response):
    print(f"Response sent for: {context.path}")
```

### User Events

#### `user_created`
Triggered when a new user is created.

**Callback Signature:**
```python
async def on_user_created(user):
    print(f"New user: {user.email}")
```

#### `user_logged_in`
Triggered when user logs in.

**Callback Signature:**
```python
async def on_user_login(user, login_method='password'):
    print(f"User {user.email} logged in via {login_method}")
```

#### `user_logged_out`
Triggered when user logs out.

**Callback Signature:**
```python
async def on_user_logout(user):
    print(f"User {user.email} logged out")
```

### Database Events

#### `model_created`
Triggered when model instance is created.

**Callback Signature:**
```python
async def on_model_created(model_class, instance):
    print(f"Created {model_class.__name__}: {instance.id}")
```

#### `model_updated`
Triggered when model instance is updated.

**Callback Signature:**
```python
async def on_model_updated(model_class, instance, old_values):
    print(f"Updated {model_class.__name__}: {instance.id}")
```

#### `model_deleted`
Triggered when model instance is deleted.

**Callback Signature:**
```python
async def on_model_deleted(model_class, instance):
    print(f"Deleted {model_class.__name__}: {instance.id}")
```

### Error Events

#### `error_occurred`
Triggered when an error occurs.

**Callback Signature:**
```python
async def on_error(error, context=None):
    print(f"Error: {error}")
```

#### `exception_caught`
Triggered when an exception is caught.

**Callback Signature:**
```python
async def on_exception(exception, traceback_info):
    print(f"Exception: {exception}")
```

---

## Plugin Types

### Middleware Plugin

```python
class MiddlewarePlugin(Plugin):
    async def initialize(self, app):
        app.middleware.append(self.process_request)
    
    async def process_request(self, context, call_next):
        # Before request
        start_time = time.time()
        
        response = await call_next(context)
        
        # After request
        duration = time.time() - start_time
        response.setdefault('headers', {})
        response['headers']['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
```

### Authentication Plugin

```python
class AuthPlugin(Plugin):
    async def initialize(self, app):
        app.auth.add_backend(CustomAuthBackend(self))
        app.middleware.insert(0, self.auth_middleware)
    
    async def auth_middleware(self, context, call_next):
        # Extract and validate authentication
        token = self.extract_token(context)
        context.user = await self.validate_token(token)
        return await call_next(context)
```

### Database Plugin

```python
class DatabasePlugin(Plugin):
    async def initialize(self, app):
        # Initialize database connection
        self.pool = await self.create_connection_pool()
        
        # Register database backend
        app.database.add_backend('custom', CustomBackend(self.pool))
        
        # Register cleanup hook
        app.hooks.register('app_shutdown', self.cleanup)
    
    async def cleanup(self):
        if self.pool:
            await self.pool.close()
```

### CLI Plugin

```python
class CLIPlugin(Plugin):
    async def initialize(self, app):
        # Register CLI commands
        app.cli.add_command(self.create_custom_command())
    
    def create_custom_command(self):
        import click
        
        @click.command()
        @click.option('--input', help='Input file')
        def custom_command(input):
            """Custom CLI command"""
            print(f"Processing {input}")
        
        return custom_command
```

---

## Configuration API

### Plugin Configuration

```python
class ConfigurablePlugin(Plugin):
    def __init__(self, **config):
        super().__init__(**config)
        
        # Required configuration
        self.api_key = config['api_key']  # Will raise KeyError if missing
        
        # Optional configuration with defaults
        self.enabled = config.get('enabled', True)
        self.timeout = config.get('timeout', 30)
        self.retry_count = config.get('retry_count', 3)
        
        # Validate configuration
        self.validate_config()
    
    def validate_config(self):
        """Validate plugin configuration"""
        if not self.api_key:
            raise ValueError("api_key is required")
        
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        
        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative")
```

### Environment-based Configuration

```python
import os

class EnvironmentPlugin(Plugin):
    def __init__(self, **config):
        # Override config with environment variables
        env_config = {
            'api_key': os.getenv('PLUGIN_API_KEY'),
            'enabled': os.getenv('PLUGIN_ENABLED', 'true').lower() == 'true',
            'debug': os.getenv('PLUGIN_DEBUG', 'false').lower() == 'true',
        }
        
        # Environment variables take precedence
        final_config = {**config, **{k: v for k, v in env_config.items() if v is not None}}
        
        super().__init__(**final_config)
```

---

## Testing Plugins

### Plugin Test Base

```python
import pytest
from pyframe.testing import TestApp
from your_plugin import YourPlugin

class TestYourPlugin:
    @pytest.fixture
    async def app_with_plugin(self):
        """Create test app with plugin"""
        app = TestApp()
        plugin = YourPlugin(test_mode=True)
        app.use_plugin(plugin)
        await app.initialize()
        return app
    
    async def test_plugin_initialization(self, app_with_plugin):
        """Test plugin initializes correctly"""
        plugin = app_with_plugin.get_plugin('your-plugin')
        assert plugin is not None
        assert plugin.enabled is True
    
    async def test_plugin_middleware(self, app_with_plugin):
        """Test plugin middleware"""
        client = app_with_plugin.test_client()
        response = await client.get('/')
        
        # Check middleware effects
        assert 'X-Plugin-Header' in response.headers
    
    async def test_plugin_hooks(self, app_with_plugin):
        """Test plugin hooks"""
        plugin = app_with_plugin.get_plugin('your-plugin')
        
        # Trigger hook and verify behavior
        await app_with_plugin.hooks.trigger('test_event', {'data': 'test'})
        
        # Assert expected side effects
        assert plugin.hook_called is True
```

### Mocking External Dependencies

```python
from unittest.mock import AsyncMock, patch

async def test_plugin_with_external_api():
    """Test plugin with mocked external API"""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {'success': True}
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        plugin = YourPlugin(api_key='test-key')
        result = await plugin.make_api_call({'data': 'test'})
        
        assert result['success'] is True
        mock_session.return_value.__aenter__.return_value.post.assert_called_once()
```

---

## Plugin Distribution

### Package Structure

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="pyframe-your-plugin",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "pyframe.plugins": [
            "your-plugin = your_plugin:create_plugin",
        ],
    },
    install_requires=[
        "pyframe-web>=0.1.0",
    ],
)
```

### Plugin Entry Point

```python
# your_plugin/__init__.py
from .plugin import YourPlugin

def create_plugin(**config):
    """Plugin factory function"""
    return YourPlugin(**config)

__version__ = "1.0.0"
__plugin_name__ = "your-plugin"
```

### Plugin Metadata

```python
# your_plugin/plugin.py
class YourPlugin(Plugin):
    name = "your-plugin"
    version = "1.0.0"
    description = "Your custom PyFrame plugin"
    author = "Your Name"
    license = "MIT"
    homepage = "https://github.com/you/pyframe-your-plugin"
    
    # Minimum PyFrame version required
    min_pyframe_version = "0.1.0"
    
    # Plugin dependencies
    dependencies = ["other-plugin>=1.0.0"]
```

This API reference provides complete documentation for building PyFrame plugins! 🔌
