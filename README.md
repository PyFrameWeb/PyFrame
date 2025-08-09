<div align="center">
  <img src="PyFrame-logo.png" alt="PyFrame Logo" width="500" height="500"/>
  
  # PyFrame - Full-Stack Python Web Framework

  **A modern, reactive web framework that allows developers to write both frontend and backend entirely in Python, with automatic compilation to efficient JavaScript for the browser.**
</div>

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 **What Makes PyFrame Special**

PyFrame revolutionizes web development by eliminating the traditional frontend/backend divide. Write your entire application in Python - from reactive UI components to database models - and PyFrame handles the rest.

```python
from pyframe import PyFrameApp, Component, Model, Field, FieldType

# Define your data model
class User(Model):
    name: str = Field(FieldType.STRING, max_length=100)
    email: str = Field(FieldType.EMAIL, unique=True)
    # ↳ Automatically generates database tables, migrations, and REST APIs!

# Create reactive UI components in Python
class UserProfile(Component):
    def render(self):
        user = self.props.get("user")
        return f"""
        <div class="profile">
            <h1>Welcome, {user.name}!</h1>
            <p>Email: {user.email}</p>
        </div>
        """
        # ↳ Automatically compiles to JavaScript for the browser!

# Set up your app
app = PyFrameApp()

@app.component_route("/profile/<user_id>")
class ProfilePage(UserProfile):
    pass

app.run()  # 🎉 Full-stack app running!
```

## ✨ **Key Features**

### 🐍 **Unified Python Development**
- Write frontend UI components entirely in Python
- Automatic compilation to optimized JavaScript
- Reactive state management with Python syntax
- No JavaScript, TypeScript, or build tools required

### 🔄 **Real-Time by Default**
- Built-in WebSocket and Server-Sent Events support
- Automatic data synchronization between server and clients
- Optimistic UI updates with conflict resolution
- Live component updates without page refreshes

### 📊 **Zero-Boilerplate Data Layer**
- Define models with Python classes and type hints
- Automatic database schema generation and migrations
- Auto-generated REST and GraphQL APIs
- Built-in validation and form generation

### 📱 **Context-Aware Adaptivity**
- Automatic device type and network speed detection
- Adaptive content delivery and optimization
- User preference detection (dark mode, reduced motion)
- Progressive enhancement for accessibility

### 🔌 **Plugin-Based Architecture**
- Lightweight core (~10-20KB) with optional plugins
- Built-in plugins for auth, caching, analytics
- Easy custom plugin development
- Hook system for extending functionality

### ⚡ **Modern Development Experience**
- Hot module replacement with file watching
- Zero-config development server
- Detailed error reporting and debugging
- AI-assisted code suggestions (optional)

## 🏗️ **Architecture Overview**

PyFrame uses a layered architecture where each component can be used independently:

```
┌─────────────────────────────────────────────────────────────┐
│  🎨 Frontend (Python → JavaScript)                         │
│  • Reactive components written in Python                   │
│  • Automatic compilation to efficient JavaScript           │
│  • Client-side hydration and state management              │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  ⚙️  Core Runtime                                          │
│  • Component lifecycle management                          │
│  • Routing and navigation                                  │
│  • Server-side rendering (SSR)                            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  🗄️  Data Layer                                           │
│  • Model definitions with automatic migrations             │
│  • Auto-generated REST/GraphQL APIs                       │
│  • Built-in validation and relationships                   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  🔌 Plugin System                                          │
│  • Authentication and authorization                        │
│  • Caching and performance optimization                    │
│  • Analytics and monitoring                               │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  🌐 Server & Deployment                                    │
│  • Context-aware adaptive rendering                        │
│  • Multiple deployment targets (serverless, edge, VPS)     │
│  • Development server with hot reload                      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start**

### Installation

```bash
pip install pyframe
```

### Using the CLI (Recommended)

PyFrame includes a command-line tool to help you get started quickly:

```bash
# Create a new project
pyframe create my-awesome-app
cd my-awesome-app

# Install dependencies
pip install -r requirements.txt

# Run the development server
python main.py
# or
pyframe run
```

Your app will be available at `http://localhost:3000` with hot reload enabled!

### Create Your First App Manually

```python
# app.py
from pyframe import PyFrameApp, Component, StatefulComponent

class Counter(StatefulComponent):
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("count", 0)
    
    def increment(self):
        count = self.get_state("count", 0)
        self.set_state("count", count + 1)
    
    def render(self):
        count = self.get_state("count", 0)
        return f"""
        <div>
            <h1>Count: {count}</h1>
            <button onclick="this.component.increment()">
                Click me!
            </button>
        </div>
        """

app = PyFrameApp()

@app.component_route("/")
class HomePage(Counter):
    pass

if __name__ == "__main__":
    app.run()
```

### Run Your App

```bash
python app.py
```

Visit `http://localhost:3000` to see your reactive counter in action! 🎉

## 📖 **Learn by Example**

### **Reactive Components**

```python
class TodoList(StatefulComponent):
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("todos", [])
        self.set_state("input_value", "")
    
    def add_todo(self):
        input_value = self.get_state("input_value", "")
        if input_value.strip():
            todos = self.get_state("todos", [])
            todos.append({"id": len(todos), "text": input_value, "done": False})
            self.set_state("todos", todos)
            self.set_state("input_value", "")
    
    def toggle_todo(self, todo_id):
        todos = self.get_state("todos", [])
        for todo in todos:
            if todo["id"] == todo_id:
                todo["done"] = not todo["done"]
        self.set_state("todos", todos)
    
    def render(self):
        todos = self.get_state("todos", [])
        input_value = self.get_state("input_value", "")
        
        todo_items = ""
        for todo in todos:
            checked = "checked" if todo["done"] else ""
            todo_items += f"""
            <li>
                <input type="checkbox" {checked} 
                       onchange="this.component.toggle_todo({todo['id']})">
                <span class="{'done' if todo['done'] else ''}">{todo['text']}</span>
            </li>
            """
        
        return f"""
        <div class="todo-app">
            <h1>Todo List</h1>
            <div class="add-todo">
                <input type="text" value="{input_value}" 
                       placeholder="Add a todo..."
                       onchange="this.component.set_state('input_value', this.value)">
                <button onclick="this.component.add_todo()">Add</button>
            </div>
            <ul class="todo-list">{todo_items}</ul>
        </div>
        """
```

### **Data Models with Auto-Generated APIs**

```python
from pyframe.data.models import Model, Field, FieldType
from datetime import datetime

class User(Model):
    username: str = Field(FieldType.STRING, unique=True, max_length=50)
    email: str = Field(FieldType.EMAIL, unique=True)
    first_name: str = Field(FieldType.STRING, max_length=50, required=False)
    last_name: str = Field(FieldType.STRING, max_length=50, required=False)
    is_active: bool = Field(FieldType.BOOLEAN, default=True)
    created_at: datetime = Field(FieldType.DATETIME, auto_now_add=True)

class Post(Model):
    title: str = Field(FieldType.STRING, max_length=200)
    content: str = Field(FieldType.TEXT)
    author_id: str = Field(FieldType.UUID, foreign_key="User")
    published: bool = Field(FieldType.BOOLEAN, default=False)
    tags: list = Field(FieldType.JSON, default=list)

# Automatically generates:
# GET /api/users - List users
# POST /api/users - Create user  
# GET /api/users/:id - Get user
# PUT /api/users/:id - Update user
# DELETE /api/users/:id - Delete user
# (Same for posts)

# Use in Python:
user = User.create(username="john", email="john@example.com")
post = Post.create(title="Hello World", content="...", author_id=user.id)
```

### **Real-Time Live Updates**

```python
class ChatRoom(StatefulComponent):
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("messages", [])
        self.set_state("input_value", "")
        
        # Subscribe to real-time updates
        room_id = props.get("room_id", "general")
        live_sync_manager.subscribe_to_channel(f"chat:{room_id}")
    
    def send_message(self):
        input_value = self.get_state("input_value", "")
        if input_value.strip():
            message = ChatMessage.create(
                content=input_value,
                room_id=self.props.get("room_id"),
                user_id=self.props.get("user_id")
            )
            # ↳ Automatically broadcasts to all connected clients!
            self.set_state("input_value", "")
    
    def render(self):
        messages = self.get_state("messages", [])
        input_value = self.get_state("input_value", "")
        
        message_list = ""
        for msg in messages:
            message_list += f"""
            <div class="message">
                <strong>{msg['username']}:</strong> {msg['content']}
            </div>
            """
        
        return f"""
        <div class="chat-room">
            <div class="messages">{message_list}</div>
            <div class="input-area">
                <input type="text" value="{input_value}"
                       onchange="this.component.set_state('input_value', this.value)"
                       onkeypress="if(event.key==='Enter') this.component.send_message()">
                <button onclick="this.component.send_message()">Send</button>
            </div>
        </div>
        """
```

### **Plugins and Authentication**

```python
from pyframe.plugins.auth_plugin import AuthPlugin, require_auth

# Configure authentication
app.register_plugin(AuthPlugin({
    "jwt_secret": "your-secret-key",
    "password_min_length": 8
}))

# Protected routes
@app.component_route("/dashboard")
@require_auth
class Dashboard(Component):
    def render(self):
        user = self.props.get("user")
        return f"""
        <div class="dashboard">
            <h1>Welcome, {user.username}!</h1>
            <p>This is your private dashboard.</p>
        </div>
        """

# Login component
class LoginForm(StatefulComponent):
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("username", "")
        self.set_state("password", "")
        self.set_state("loading", False)
    
    async def handle_login(self):
        self.set_state("loading", True)
        
        username = self.get_state("username", "")
        password = self.get_state("password", "")
        
        # Make API call to login endpoint
        response = await fetch("/auth/login", {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"username": username, "password": password})
        })
        
        if response.ok:
            # Redirect to dashboard
            window.location.href = "/dashboard"
        else:
            self.set_state("loading", False)
            # Show error message
    
    def render(self):
        username = self.get_state("username", "")
        password = self.get_state("password", "")
        loading = self.get_state("loading", False)
        
        return f"""
        <form class="login-form" onsubmit="this.component.handle_login(); return false;">
            <h2>Login</h2>
            <input type="text" placeholder="Username" value="{username}"
                   onchange="this.component.set_state('username', this.value)">
            <input type="password" placeholder="Password" value="{password}"
                   onchange="this.component.set_state('password', this.value)">
            <button type="submit" {'disabled' if loading else ''}>
                {'Logging in...' if loading else 'Login'}
            </button>
        </form>
        """
```

## 🌟 **Live Demo**

Explore a complete blog application built with PyFrame:

```bash
git clone https://github.com/pyframe/pyframe.git
cd pyframe/examples/blog_app
pip install -r requirements.txt
python main.py
```

Visit `http://localhost:3000` to see:
- Reactive Python components
- Real-time comments
- Auto-generated APIs
- Adaptive rendering
- Authentication system
- Hot reload in action

## 📚 **Documentation**

### **Core Concepts**
- [Components and State Management](docs/components.md)
- [Routing and Navigation](docs/routing.md)
- [Data Models and APIs](docs/data-layer.md)
- [Real-Time Features](docs/realtime.md)

### **Advanced Topics**
- [Plugin Development](docs/plugins.md)
- [Custom Hooks](docs/hooks.md)
- [Deployment Guide](docs/deployment.md)
- [Performance Optimization](docs/performance.md)

### **API Reference**
- [Component API](docs/api/components.md)
- [Model API](docs/api/models.md)
- [Plugin API](docs/api/plugins.md)
- [Server API](docs/api/server.md)

## 🔧 **Development**

### **Requirements**
- Python 3.8+
- Modern web browser with JavaScript enabled

### **Dependencies**
- `asyncio` - Asynchronous programming
- `websockets` - Real-time communication
- `watchdog` - File system monitoring
- `PyJWT` - JSON Web Tokens

### **Development Setup**

```bash
# Clone the repository
git clone https://github.com/pyframe/pyframe.git
cd pyframe

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Run the example app
cd examples/blog_app
python main.py
```

## 🚢 **Deployment**

PyFrame applications can be deployed anywhere Python runs:

### **Traditional Servers**
```python
from pyframe.deployment.wsgi import create_wsgi_app

# WSGI for Apache, Gunicorn, uWSGI
application = create_wsgi_app(app)
```

### **ASGI Servers**
```python
from pyframe.deployment.asgi import create_asgi_app

# ASGI for Uvicorn, Daphne, Hypercorn
application = create_asgi_app(app)
```

### **Serverless Functions**
```python
# AWS Lambda, Vercel, Netlify Functions
def lambda_handler(event, context):
    return app.handle_serverless_request(event, context)
```

### **Edge Computing**
```python
# Cloudflare Workers, Deno Deploy
app.configure_for_edge_deployment()
```

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Philosophy**
- **Python-First**: Everything should be writable in Python
- **Zero Config**: Sensible defaults with optional customization
- **Performance**: Fast development, fast runtime
- **Accessibility**: Progressive enhancement and WCAG compliance
- **Developer Experience**: Great error messages and debugging tools

## 📄 **License**

MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

PyFrame is inspired by:
- **React** - Component-based architecture
- **Django** - Batteries-included philosophy  
- **FastAPI** - Modern Python web framework design
- **Next.js** - Full-stack development experience
- **Phoenix LiveView** - Real-time server-rendered UI

## 💬 **Community**

- [GitHub Discussions](https://github.com/pyframe/pyframe/discussions) - Questions and ideas
- [Discord Server](https://discord.gg/pyframe) - Real-time chat
- [Twitter](https://twitter.com/pyframe) - Updates and announcements
- [Examples](https://github.com/PyFrameWeb/PyFrame/tree/main/examples) - Sample applications and tutorials

---

**Ready to build the future of web development with Python?** 🐍✨

```bash
pip install pyframe
```

[Get Started](https://github.com/PyFrameWeb/PyFrame/blob/main/docs/core-concepts.md) | [Examples](https://github.com/PyFrameWeb/PyFrame/tree/main/examples) | [API Docs](https://github.com/PyFrameWeb/PyFrame/tree/main/docs/api-reference)
