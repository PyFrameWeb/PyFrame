# Component API Reference

Complete reference for PyFrame's component system.

## Base Component Class

### `Component`

The base class for all PyFrame components.

```python
from pyframe import Component

class MyComponent(Component):
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        return "<div>Hello World</div>"
```

#### Methods

##### `__init__(self, **props)`
Initialize the component with props.

**Parameters:**
- `**props` - Arbitrary keyword arguments passed as component properties

##### `render(self) -> str`
Render the component to HTML.

**Returns:**
- `str` - HTML string representation of the component

**Example:**
```python
def render(self):
    name = self.props.get('name', 'World')
    return f"<h1>Hello, {name}!</h1>"
```

##### `get_styles(self) -> str`
Return CSS styles for the component.

**Returns:**
- `str` - CSS styles as a string

**Example:**
```python
def get_styles(self):
    return """
    .my-component {
        background: #f0f0f0;
        padding: 20px;
        border-radius: 8px;
    }
    """
```

##### `get_scripts(self) -> str`
Return JavaScript code for the component.

**Returns:**
- `str` - JavaScript code as a string

**Example:**
```python
def get_scripts(self):
    return """
    function handleClick() {
        alert('Button clicked!');
    }
    """
```

#### Properties

##### `props: dict`
Dictionary containing component properties passed during initialization.

```python
class Greeting(Component):
    def render(self):
        name = self.props.get('name', 'Guest')
        age = self.props.get('age')
        
        greeting = f"Hello, {name}!"
        if age:
            greeting += f" You are {age} years old."
        
        return f"<p>{greeting}</p>"

# Usage
component = Greeting(name="Alice", age=25)
```

---

## StatefulComponent Class

### `StatefulComponent`

Component with internal state management capabilities.

```python
from pyframe import StatefulComponent, State

class Counter(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({'count': 0})
    
    def increment(self):
        current = self.state.get('count')
        self.state.update('count', current + 1)
    
    def render(self):
        count = self.state.get('count')
        return f"""
        <div>
            <p>Count: {count}</p>
            <button onclick="this.component.increment()">+1</button>
        </div>
        """
```

#### Methods

##### `__init__(self, **props)`
Initialize the stateful component.

**Parameters:**
- `**props` - Component properties

**Note:** Must call `super().__init__(**props)` and initialize `self.state`

##### Lifecycle Methods

##### `async component_did_mount(self)`
Called after the component is first rendered and mounted.

```python
async def component_did_mount(self):
    # Load initial data
    data = await self.fetch_user_data()
    self.state.update('user', data)
```

##### `async component_will_update(self, new_props, new_state)`
Called before component updates with new props or state.

**Parameters:**
- `new_props: dict` - New properties
- `new_state: dict` - New state values

```python
async def component_will_update(self, new_props, new_state):
    if new_props.get('user_id') != self.props.get('user_id'):
        # User changed, fetch new data
        user_data = await self.fetch_user(new_props['user_id'])
        new_state['user'] = user_data
```

##### `component_will_unmount(self)`
Called before component is removed from the DOM.

```python
def component_will_unmount(self):
    # Cleanup resources
    if hasattr(self, 'websocket'):
        self.websocket.close()
    
    if hasattr(self, 'timer'):
        self.timer.cancel()
```

#### Properties

##### `state: State`
Component's internal state object.

```python
class TodoList(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'todos': [],
            'filter': 'all',
            'new_todo': ''
        })
    
    def add_todo(self, text):
        todos = self.state.get('todos')
        todos.append({
            'id': len(todos) + 1,
            'text': text,
            'completed': False
        })
        self.state.update('todos', todos)
```

---

## State Class

### `State`

Manages component state with change tracking and persistence.

```python
from pyframe import State

# Basic usage
state = State({'count': 0, 'name': 'Alice'})

# With persistence
state = State({'theme': 'dark'}, persist=True)

# With validation
def validate_count(value):
    if value < 0:
        raise ValueError("Count cannot be negative")
    return value

state = State(
    {'count': 0},
    validators={'count': validate_count}
)
```

#### Methods

##### `__init__(self, initial_data=None, persist=False, validators=None)`
Initialize state object.

**Parameters:**
- `initial_data: dict` - Initial state values (default: `{}`)
- `persist: bool` - Whether to persist state to localStorage (default: `False`)
- `validators: dict` - Field validators (default: `None`)

##### `get(self, key, default=None)`
Get a state value.

**Parameters:**
- `key: str` - State key
- `default: Any` - Default value if key doesn't exist

**Returns:**
- `Any` - State value or default

```python
count = self.state.get('count', 0)
user = self.state.get('user')  # Returns None if not set
```

##### `update(self, key, value)`
Update a single state value.

**Parameters:**
- `key: str` - State key
- `value: Any` - New value

```python
self.state.update('count', 5)
self.state.update('user', {'name': 'Alice', 'email': 'alice@example.com'})
```

##### `set_multiple(self, updates)`
Update multiple state values at once.

**Parameters:**
- `updates: dict` - Dictionary of key-value pairs to update

```python
self.state.set_multiple({
    'loading': False,
    'data': response_data,
    'error': None
})
```

##### `delete(self, key)`
Remove a key from state.

**Parameters:**
- `key: str` - State key to remove

```python
self.state.delete('temporary_data')
```

##### `clear(self)`
Clear all state data.

```python
self.state.clear()
```

##### `to_dict(self)`
Convert state to a dictionary.

**Returns:**
- `dict` - State as dictionary

```python
state_dict = self.state.to_dict()
print(state_dict)  # {'count': 5, 'name': 'Alice'}
```

#### Events

##### `on_change(self, callback)`
Register a callback for state changes.

**Parameters:**
- `callback: callable` - Function called when state changes

```python
def handle_state_change(key, old_value, new_value):
    print(f"State changed: {key} = {old_value} -> {new_value}")

self.state.on_change(handle_state_change)
```

---

## Connected Components

### `ConnectedComponent`

Component that automatically syncs with database models.

```python
from pyframe import ConnectedComponent, Model

class User(Model):
    name = Field(FieldType.STRING, max_length=100)
    email = Field(FieldType.EMAIL)

class UserProfile(ConnectedComponent):
    model = User
    
    def __init__(self, user_id, **props):
        super().__init__(**props)
        self.user_id = user_id
        self.load_data()
    
    async def load_data(self):
        self.user = await User.get(self.user_id)
        self.state.update('user', self.user.to_dict())
    
    def render(self):
        user = self.state.get('user', {})
        return f"""
        <div class="user-profile">
            <h2>{user.get('name', 'Unknown')}</h2>
            <p>{user.get('email', '')}</p>
        </div>
        """
```

#### Properties

##### `model: Model`
The database model this component is connected to.

##### `auto_sync: bool`
Whether to automatically sync with database changes (default: `True`).

#### Methods

##### `async reload_data(self)`
Reload data from the database.

```python
async def reload_data(self):
    fresh_data = await self.model.get(self.object_id)
    self.state.update('data', fresh_data.to_dict())
```

##### `async save_changes(self, data)`
Save changes back to the database.

**Parameters:**
- `data: dict` - Data to save

```python
async def save_changes(self, form_data):
    await self.user.update(**form_data)
    await self.reload_data()
```

---

## Component Decorators

### `@cached_component`

Cache component render output.

```python
from pyframe.decorators import cached_component

@cached_component(timeout=300)  # Cache for 5 minutes
class ExpensiveComponent(Component):
    def render(self):
        # Expensive computation
        return self.complex_calculation()
```

**Parameters:**
- `timeout: int` - Cache timeout in seconds (default: `300`)
- `key_func: callable` - Function to generate cache key (optional)

### `@requires_auth`

Require authentication to render component.

```python
from pyframe.decorators import requires_auth

@requires_auth
class ProtectedComponent(Component):
    def render(self):
        user = self.context.user
        return f"<h1>Welcome, {user.name}!</h1>"
```

### `@rate_limited`

Rate limit component rendering.

```python
from pyframe.decorators import rate_limited

@rate_limited(max_requests=10, window=60)  # 10 requests per minute
class APIComponent(Component):
    def render(self):
        return self.fetch_external_data()
```

---

## Component Utilities

### `render_component(component_class, **props)`

Render a component with given props.

```python
from pyframe.utils import render_component

html = render_component(MyComponent, name="Alice", age=25)
```

### `component_to_dict(component)`

Convert component to dictionary representation.

```python
from pyframe.utils import component_to_dict

component = MyComponent(name="Alice")
data = component_to_dict(component)
# {'type': 'MyComponent', 'props': {'name': 'Alice'}, 'state': {}}
```

### `register_component(name, component_class)`

Register a component globally.

```python
from pyframe.registry import register_component

register_component('my-widget', MyWidget)

# Use in templates
html = "{% raw %}{{ component('my-widget', name='Alice') }}{% endraw %}"
```

---

## Error Handling

### Component Error Boundaries

```python
class ErrorBoundary(Component):
    def __init__(self, **props):
        super().__init__(**props)
        self.has_error = False
        self.error_info = None
    
    def component_did_catch(self, error, error_info):
        self.has_error = True
        self.error_info = error_info
        
        # Log error
        print(f"Component error: {error}")
        print(f"Error info: {error_info}")
    
    def render(self):
        if self.has_error:
            return """
            <div class="error-boundary">
                <h2>Something went wrong</h2>
                <p>Please try refreshing the page.</p>
            </div>
            """
        
        # Render children normally
        return self.props.get('children', '')

# Usage
error_boundary = ErrorBoundary(children=problematic_component.render())
```

---

## Best Practices

### 1. Component Naming
```python
# Good: PascalCase for component classes
class UserProfile(Component):
    pass

class ShoppingCart(StatefulComponent):
    pass

# Good: Descriptive names
class ProductCard(Component):
    pass

class NavigationMenu(Component):
    pass
```

### 2. Props Validation
```python
class UserCard(Component):
    def __init__(self, **props):
        super().__init__(**props)
        
        # Validate required props
        if 'user' not in props:
            raise ValueError("UserCard requires 'user' prop")
        
        # Validate prop types
        user = props['user']
        if not isinstance(user, dict):
            raise TypeError("'user' prop must be a dictionary")
        
        if 'name' not in user:
            raise ValueError("User must have a 'name' field")
```

### 3. State Management
```python
class TodoApp(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        
        # Initialize with sensible defaults
        self.state = State({
            'todos': [],
            'filter': 'all',
            'loading': False,
            'error': None
        })
    
    def handle_error(self, error):
        self.state.set_multiple({
            'loading': False,
            'error': str(error)
        })
    
    async def load_todos(self):
        try:
            self.state.update('loading', True)
            self.state.update('error', None)
            
            todos = await self.fetch_todos()
            self.state.update('todos', todos)
        except Exception as e:
            self.handle_error(e)
        finally:
            self.state.update('loading', False)
```

### 4. Performance Optimization
```python
# Use cached_component for expensive renders
@cached_component(timeout=600)
class Dashboard(Component):
    def render(self):
        return self.generate_complex_dashboard()

# Minimize state updates
class OptimizedComponent(StatefulComponent):
    def update_multiple_fields(self, data):
        # Good: Single state update
        self.state.set_multiple(data)
        
        # Bad: Multiple state updates
        # for key, value in data.items():
        #     self.state.update(key, value)
```

This completes the Component API reference. Components are the building blocks of PyFrame applications! 🧱
