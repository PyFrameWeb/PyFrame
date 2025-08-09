# Core Concepts

Welcome to PyFrame! This guide covers the fundamental concepts that make PyFrame a revolutionary Python web framework.

## 🐍 Python-First Philosophy

PyFrame is built on the principle that you shouldn't need to learn multiple languages to build modern web applications. Write everything in Python - from UI components to database models.

```python
from pyframe import PyFrameApp, Component, StatefulComponent

# Frontend component - pure Python!
class WelcomeMessage(Component):
    def render(self):
        name = self.props.get('name', 'World')
        return f"<h1>Hello, {name}!</h1>"

# Backend route - same language!
@app.route('/api/users')
async def get_users(context):
    users = await User.all()
    return {'users': [user.to_dict() for user in users]}
```

## 🔄 Reactive Architecture

PyFrame automatically handles state synchronization between frontend and backend, ensuring your UI stays in sync with your data.

### State Management
- **Component State**: Local state for individual components
- **Global State**: Application-wide state management
- **Database State**: Automatic synchronization with data models

```python
class Counter(StatefulComponent):
    def __init__(self):
        super().__init__()
        self.state = State({'count': 0})
    
    def increment(self):
        current = self.state.get('count')
        self.state.update('count', current + 1)
        # UI automatically updates!
```

## 🏗️ Component Architecture

### Component Types

1. **Static Components**: Render content without state
2. **Stateful Components**: Manage internal state and lifecycle
3. **Connected Components**: Automatically sync with database models

```python
# Static Component
class Header(Component):
    def render(self):
        return "<header><h1>My App</h1></header>"

# Stateful Component
class TodoList(StatefulComponent):
    def __init__(self):
        super().__init__()
        self.state = State({'todos': []})
    
    def add_todo(self, text):
        todos = self.state.get('todos')
        todos.append({'id': len(todos), 'text': text, 'done': False})
        self.state.update('todos', todos)

# Connected Component
class UserProfile(Component):
    async def render(self):
        user = await User.get(self.props['user_id'])
        return f"""
        <div class="profile">
            <h2>{user.name}</h2>
            <p>{user.email}</p>
        </div>
        """
```

## 🛣️ Routing System

PyFrame provides flexible routing that works seamlessly with components.

### Route Types
- **Static Routes**: Fixed URLs
- **Dynamic Routes**: URL parameters
- **Component Routes**: Direct component rendering
- **API Routes**: JSON endpoints

```python
# Static route
@app.route('/')
async def home(context):
    return HomePage().render()

# Dynamic route
@app.route('/user/<user_id>')
async def user_profile(context):
    user_id = context.params['user_id']
    return UserProfile(user_id=user_id).render()

# Component route
@app.component_route('/dashboard')
class Dashboard(StatefulComponent):
    pass
```

## 💾 Data Layer

PyFrame's data layer automatically generates APIs and handles database operations.

### Model Definition
```python
from pyframe import Model, Field, FieldType

class User(Model):
    name = Field(FieldType.STRING, max_length=100)
    email = Field(FieldType.EMAIL, unique=True)
    created_at = Field(FieldType.DATETIME, auto_now_add=True)
    
    # Automatically generates:
    # - Database table
    # - Migration files
    # - REST API endpoints
    # - Validation logic
```

### Automatic API Generation
```python
# These endpoints are automatically created:
# GET /api/users - List all users
# POST /api/users - Create user
# GET /api/users/{id} - Get specific user
# PUT /api/users/{id} - Update user
# DELETE /api/users/{id} - Delete user
```

## 🔥 Hot Reload System

PyFrame's hot reload system provides instant feedback during development.

### What Gets Reloaded
- **Python Components**: UI updates instantly
- **Route Handlers**: Backend logic refreshes
- **Database Models**: Schema changes applied
- **Static Assets**: CSS/JS files reload

```python
# Enable hot reload in development
config = PyFrameConfig(
    debug=True,
    hot_reload=True,
    host="localhost",
    port=3000
)
```

## ⚡ Performance Features

### Automatic Optimizations
- **Component Caching**: Intelligent caching of rendered components
- **Database Query Optimization**: Automatic query batching and caching
- **Static Asset Optimization**: Minification and compression
- **Code Splitting**: Automatic JavaScript bundle optimization

### Manual Optimizations
```python
# Component-level caching
class ExpensiveComponent(Component):
    cache_key = "expensive-data"
    cache_timeout = 300  # 5 minutes
    
    def render(self):
        # This will be cached automatically
        return self.expensive_computation()

# Database query optimization
users = await User.select_related('profile').all()  # Joins automatically
```

## 🔌 Plugin System

Extend PyFrame with powerful plugins for authentication, caching, analytics, and more.

```python
from pyframe.plugins import AuthPlugin, CachePlugin

app = PyFrameApp()

# Add authentication
app.use_plugin(AuthPlugin(
    providers=['github', 'google'],
    secret_key='your-secret-key'
))

# Add caching
app.use_plugin(CachePlugin(
    backend='redis',
    default_timeout=300
))
```

## 🌐 Real-Time Features

Built-in WebSocket support for real-time applications.

```python
from pyframe.realtime import WebSocketManager

ws_manager = WebSocketManager()

# Real-time data updates
@app.websocket('/ws/updates')
async def handle_updates(websocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast to all connected clients
            await ws_manager.broadcast(data)
    except:
        await ws_manager.disconnect(websocket)
```

## 📚 Next Steps

- [Components and State Management](components-state.md)
- [Routing and Navigation](routing-navigation.md)
- [Data Models and APIs](data-models-apis.md)
- [Real-Time Features](realtime-features.md)
- [API Reference](api-reference/)

## 🤝 Philosophy

PyFrame believes that:
- **Simplicity**: Complex problems should have simple solutions
- **Productivity**: Developers should focus on business logic, not boilerplate
- **Performance**: Great performance should be the default, not an afterthought
- **Community**: Open source collaboration drives innovation

Welcome to the future of Python web development! 🚀
