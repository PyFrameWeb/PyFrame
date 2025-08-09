# Components and State Management

PyFrame's component system is inspired by React but designed specifically for Python developers. This guide covers everything you need to know about building reactive UIs with PyFrame.

## 🧱 Component Basics

### Component Types

PyFrame provides three main component types:

1. **Component**: Static components for rendering content
2. **StatefulComponent**: Components with internal state management
3. **ConnectedComponent**: Components connected to database models

## 📦 Static Components

Static components are the simplest form - they render content without managing state.

```python
from pyframe import Component

class Header(Component):
    def render(self):
        title = self.props.get('title', 'PyFrame App')
        return f"""
        <header class="app-header">
            <h1>{title}</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
        </header>
        """

class Button(Component):
    def render(self):
        text = self.props.get('text', 'Click me')
        onclick = self.props.get('onclick', '')
        disabled = self.props.get('disabled', False)
        
        disabled_attr = 'disabled' if disabled else ''
        
        return f"""
        <button onclick="{onclick}" {disabled_attr} class="btn">
            {text}
        </button>
        """
```

### Using Components

```python
# In a route or another component
header = Header(title="My Awesome App")
button = Button(text="Save", onclick="handleSave()")

html = f"""
<div>
    {header.render()}
    <main>
        <p>Welcome to my app!</p>
        {button.render()}
    </main>
</div>
"""
```

## 🔄 Stateful Components

Stateful components manage internal state and can react to user interactions.

### Basic State Management

```python
from pyframe import StatefulComponent, State

class Counter(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        initial_count = props.get('initial_count', 0)
        self.state = State({
            'count': initial_count,
            'incrementBy': 1
        })
    
    def increment(self):
        current = self.state.get('count')
        increment_by = self.state.get('incrementBy')
        self.state.update('count', current + increment_by)
    
    def decrement(self):
        current = self.state.get('count')
        increment_by = self.state.get('incrementBy')
        self.state.update('count', current - increment_by)
    
    def set_increment_by(self, value):
        self.state.update('incrementBy', int(value))
    
    def render(self):
        count = self.state.get('count')
        increment_by = self.state.get('incrementBy')
        
        return f"""
        <div class="counter">
            <h2>Counter: {count}</h2>
            <div class="controls">
                <button onclick="this.component.decrement()">-</button>
                <button onclick="this.component.increment()">+</button>
            </div>
            <div class="settings">
                <label>Increment by:</label>
                <input type="number" value="{increment_by}" 
                       onchange="this.component.set_increment_by(this.value)">
            </div>
        </div>
        """
```

### Advanced State Management

```python
class TodoApp(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'todos': [],
            'new_todo_text': '',
            'filter': 'all'  # all, active, completed
        })
    
    def add_todo(self):
        text = self.state.get('new_todo_text').strip()
        if not text:
            return
        
        todos = self.state.get('todos')
        new_todo = {
            'id': len(todos) + 1,
            'text': text,
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        
        todos.append(new_todo)
        self.state.update('todos', todos)
        self.state.update('new_todo_text', '')
    
    def toggle_todo(self, todo_id):
        todos = self.state.get('todos')
        for todo in todos:
            if todo['id'] == todo_id:
                todo['completed'] = not todo['completed']
                break
        self.state.update('todos', todos)
    
    def delete_todo(self, todo_id):
        todos = self.state.get('todos')
        todos = [todo for todo in todos if todo['id'] != todo_id]
        self.state.update('todos', todos)
    
    def set_filter(self, filter_type):
        self.state.update('filter', filter_type)
    
    def get_filtered_todos(self):
        todos = self.state.get('todos')
        filter_type = self.state.get('filter')
        
        if filter_type == 'active':
            return [todo for todo in todos if not todo['completed']]
        elif filter_type == 'completed':
            return [todo for todo in todos if todo['completed']]
        return todos
    
    def render(self):
        new_todo_text = self.state.get('new_todo_text')
        filter_type = self.state.get('filter')
        filtered_todos = self.get_filtered_todos()
        
        todo_items = ''
        for todo in filtered_todos:
            checked = 'checked' if todo['completed'] else ''
            completed_class = 'completed' if todo['completed'] else ''
            
            todo_items += f"""
            <li class="todo-item {completed_class}">
                <input type="checkbox" {checked} 
                       onchange="this.component.toggle_todo({todo['id']})">
                <span class="todo-text">{todo['text']}</span>
                <button onclick="this.component.delete_todo({todo['id']})" 
                        class="delete-btn">×</button>
            </li>
            """
        
        return f"""
        <div class="todo-app">
            <h1>Todo App</h1>
            
            <div class="add-todo">
                <input type="text" 
                       value="{new_todo_text}"
                       placeholder="What needs to be done?"
                       onchange="this.component.state.update('new_todo_text', this.value)"
                       onkeypress="if(event.key==='Enter') this.component.add_todo()">
                <button onclick="this.component.add_todo()">Add</button>
            </div>
            
            <div class="filters">
                <button onclick="this.component.set_filter('all')" 
                        class="{'active' if filter_type == 'all' else ''}">All</button>
                <button onclick="this.component.set_filter('active')" 
                        class="{'active' if filter_type == 'active' else ''}">Active</button>
                <button onclick="this.component.set_filter('completed')" 
                        class="{'active' if filter_type == 'completed' else ''}">Completed</button>
            </div>
            
            <ul class="todo-list">
                {todo_items}
            </ul>
        </div>
        """
```

## 🔗 Connected Components

Connected components automatically sync with database models.

```python
from pyframe import ConnectedComponent, Model, Field, FieldType

class User(Model):
    name = Field(FieldType.STRING, max_length=100)
    email = Field(FieldType.EMAIL, unique=True)
    avatar_url = Field(FieldType.URL, null=True)

class UserProfile(ConnectedComponent):
    model = User
    
    def __init__(self, user_id, **props):
        super().__init__(**props)
        self.user_id = user_id
        self.load_data()
    
    async def load_data(self):
        # Automatically loads and syncs with database
        self.user = await User.get(self.user_id)
        self.state.update('user', self.user.to_dict())
    
    async def update_profile(self, data):
        # Updates database and local state
        await self.user.update(**data)
        self.state.update('user', self.user.to_dict())
    
    def render(self):
        user = self.state.get('user', {})
        
        return f"""
        <div class="user-profile">
            <img src="{user.get('avatar_url', '/default-avatar.png')}" 
                 alt="Avatar" class="avatar">
            <h2>{user.get('name', 'Unknown')}</h2>
            <p>{user.get('email', '')}</p>
            
            <form onsubmit="this.component.handleUpdate(event)">
                <input name="name" value="{user.get('name', '')}" placeholder="Name">
                <input name="email" value="{user.get('email', '')}" placeholder="Email">
                <button type="submit">Update Profile</button>
            </form>
        </div>
        """
    
    def handle_update(self, event):
        # Extract form data and update
        form_data = self.extract_form_data(event.target)
        self.update_profile(form_data)
```

## 🎛️ State Management Patterns

### Local State
Best for component-specific data that doesn't need to be shared.

```python
class SearchBox(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'query': '',
            'results': [],
            'loading': False
        })
```

### Shared State
For data that needs to be shared between components.

```python
from pyframe.state import GlobalState

# Global state instance
app_state = GlobalState({
    'user': None,
    'theme': 'light',
    'notifications': []
})

class NavBar(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        # Connect to global state
        self.global_state = app_state
        self.state = State({
            'menu_open': False
        })
    
    def render(self):
        user = self.global_state.get('user')
        theme = self.global_state.get('theme')
        
        return f"""
        <nav class="navbar theme-{theme}">
            {f"Welcome, {user['name']}" if user else "Please log in"}
        </nav>
        """
```

### State Persistence
Automatically save state to localStorage.

```python
class Settings(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'theme': 'light',
            'language': 'en',
            'notifications_enabled': True
        }, persist=True)  # Automatically saves to localStorage
```

## 🎯 Component Lifecycle

### Lifecycle Methods

```python
class AdvancedComponent(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({'data': None})
    
    async def component_did_mount(self):
        """Called after component is first rendered"""
        data = await self.fetch_data()
        self.state.update('data', data)
    
    async def component_will_update(self, new_props, new_state):
        """Called before component updates"""
        if new_props.get('user_id') != self.props.get('user_id'):
            # User changed, fetch new data
            data = await self.fetch_data(new_props['user_id'])
            new_state['data'] = data
    
    def component_will_unmount(self):
        """Called before component is removed"""
        # Cleanup resources
        self.cleanup_websockets()
        self.cancel_pending_requests()
```

## 🔧 Component Best Practices

### 1. Keep Components Small and Focused
```python
# Good: Single responsibility
class UserAvatar(Component):
    def render(self):
        user = self.props['user']
        return f'<img src="{user.avatar}" alt="{user.name}">'

# Good: Focused on one task
class UserName(Component):
    def render(self):
        user = self.props['user']
        return f'<span class="username">{user.name}</span>'
```

### 2. Use Props for Configuration
```python
class Modal(Component):
    def render(self):
        title = self.props.get('title', 'Modal')
        size = self.props.get('size', 'medium')
        closable = self.props.get('closable', True)
        content = self.props.get('content', '')
        
        close_btn = '<button onclick="closeModal()">×</button>' if closable else ''
        
        return f"""
        <div class="modal modal-{size}">
            <div class="modal-header">
                <h3>{title}</h3>
                {close_btn}
            </div>
            <div class="modal-content">
                {content}
            </div>
        </div>
        """
```

### 3. Handle Errors Gracefully
```python
class DataDisplay(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'data': None,
            'loading': True,
            'error': None
        })
    
    async def load_data(self):
        try:
            self.state.update('loading', True)
            self.state.update('error', None)
            
            data = await self.fetch_data()
            self.state.update('data', data)
        except Exception as e:
            self.state.update('error', str(e))
        finally:
            self.state.update('loading', False)
    
    def render(self):
        if self.state.get('loading'):
            return '<div class="loading">Loading...</div>'
        
        if self.state.get('error'):
            error = self.state.get('error')
            return f'<div class="error">Error: {error}</div>'
        
        data = self.state.get('data')
        return f'<div class="data">{data}</div>'
```

## 📚 Next Steps

- [Routing and Navigation](routing-navigation.md)
- [Data Models and APIs](data-models-apis.md)
- [Real-Time Features](realtime-features.md)
- [Component API Reference](api-reference/component-api.md)

The component system is the heart of PyFrame - master it and you'll be building powerful, reactive web applications in no time! 🚀
