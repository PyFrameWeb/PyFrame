# PyFrame Blog - Sample Application

A comprehensive blog application demonstrating all PyFrame features, including reactive Python components, real-time updates, automatic API generation, and adaptive rendering.

## Features Demonstrated

### 🐍 **Unified Python Frontend & Backend**
- Write UI components entirely in Python
- Automatic compilation to efficient JavaScript
- Reactive state management with Python syntax
- Server-side rendering with client-side hydration

### ⚡ **Real-time Updates**
- Live comment system using WebSockets
- Automatic UI updates when data changes
- Optimistic updates with conflict resolution

### 🔄 **Zero-Boilerplate Data Layer**
- Define models with Python classes
- Automatic database schema generation
- Auto-generated REST APIs for all models
- Built-in validation and migrations

### 📱 **Context-Aware Adaptivity**
- Automatic device type detection
- Network-aware content delivery
- Responsive design optimization
- Dark mode and accessibility support

### 🔌 **Plugin System**
- Authentication with JWT tokens
- Caching for improved performance
- Analytics and metrics collection
- Extensible architecture

### 🛠️ **Development Tools**
- Hot module replacement
- File watching and auto-reload
- Error overlay and debugging
- Performance monitoring

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python main.py
   ```

3. **Open Your Browser**
   Navigate to http://localhost:3000

## Application Structure

```
blog_app/
├── main.py              # Main application with all components
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── blog.db            # SQLite database (auto-created)
```

## Key Components

### **Data Models**
- `BlogPost` - Blog posts with tags, view counts, and publishing
- `Comment` - Threaded comments with real-time updates
- `AuthUser` - User authentication and profiles

### **UI Components**
- `BlogLayout` - Main layout with responsive navigation
- `PostCard` - Reusable post display component
- `CommentList` - Real-time comment system
- `SearchBox` - Live search with debouncing

### **Page Components**
- `HomePage` - Landing page with recent posts
- `PostDetailPage` - Individual post view with comments

## Features in Action

### **Reactive Components**
Components automatically update when state changes:

```python
class Counter(StatefulComponent):
    def __init__(self):
        super().__init__()
        self.set_state("count", 0)
    
    def increment(self):
        count = self.get_state("count", 0)
        self.set_state("count", count + 1)
    
    def render(self):
        count = self.get_state("count", 0)
        return f'<button onclick="this.component.increment()">Count: {count}</button>'
```

### **Automatic API Generation**
Models automatically get REST endpoints:

```python
class BlogPost(Model):
    title: str = Field(FieldType.STRING, max_length=200)
    content: str = Field(FieldType.TEXT)
    # Automatically generates:
    # GET /api/blogposts - List posts
    # POST /api/blogposts - Create post
    # GET /api/blogposts/:id - Get post
    # PUT /api/blogposts/:id - Update post
    # DELETE /api/blogposts/:id - Delete post
```

### **Real-time Updates**
Changes automatically sync across all connected clients:

```python
def save(self):
    result = super().save()
    # Automatically notifies all clients
    asyncio.create_task(
        live_sync_manager.sync_model_change(self, 'update')
    )
    return result
```

### **Context-Aware Rendering**
Content automatically adapts to client capabilities:

```python
# Automatically detects:
# - Device type (mobile, tablet, desktop)
# - Network speed (slow, moderate, fast)
# - User preferences (dark mode, reduced motion)
# - Browser capabilities (WebP, AVIF support)

# Renders accordingly:
# - Optimized images for mobile
# - Reduced animations for slow connections
# - Dark mode CSS for user preference
```

## Authentication

The app includes a complete authentication system:

- **Registration**: `/auth/register`
- **Login**: `/auth/login`
- **Profile**: `/auth/profile`
- **Logout**: `/auth/logout`

Default admin account:
- Username: `admin`
- Password: `admin123`

## API Endpoints

All models automatically get REST APIs:

### Blog Posts
- `GET /api/blogposts` - List all posts
- `POST /api/blogposts` - Create new post
- `GET /api/blogposts/:id` - Get specific post
- `PUT /api/blogposts/:id` - Update post
- `DELETE /api/blogposts/:id` - Delete post

### Comments
- `GET /api/comments` - List all comments
- `POST /api/comments` - Create new comment
- `GET /api/comments/:id` - Get specific comment

### Users
- `GET /api/authusers` - List users (admin only)
- `GET /api/authusers/:id` - Get user details

## Real-time Features

### **Live Comments**
- Comments appear instantly for all users
- No page refresh required
- Automatic conflict resolution

### **Live Search**
- Search results update as you type
- Debounced to avoid excessive requests
- Highlights matching content

### **View Counter**
- Page views update in real-time
- Tracks unique visitors
- No database polling needed

## Development Mode

The development server includes:

- **Hot Reload**: Changes to Python files automatically reload the page
- **Error Overlay**: Detailed error information displayed in browser
- **Performance Monitoring**: Request timing and component render metrics
- **WebSocket Debugging**: Real-time connection status and messages

## Production Deployment

For production deployment:

1. **Update Configuration**
   ```python
   config = PyFrameConfig(
       debug=False,
       hot_reload=False,
       host="0.0.0.0",
       port=80,
       database_url="postgresql://user:pass@localhost/blog"
   )
   ```

2. **Use Production Database**
   - Replace SQLite with PostgreSQL/MySQL
   - Configure connection pooling
   - Set up database backups

3. **Enable Security Features**
   - Set strong JWT secret keys
   - Enable HTTPS/SSL
   - Configure CSRF protection
   - Set up rate limiting

4. **Optimize Performance**
   - Enable caching plugins
   - Use CDN for static assets
   - Configure load balancing
   - Monitor with analytics

## Architecture Overview

PyFrame uses a plugin-based architecture where the core is lightweight (~10-20KB) and features are added through plugins:

```
┌─────────────────┐
│   Frontend      │ ← Python components compiled to JS
├─────────────────┤
│   Core Runtime  │ ← Reactive system, routing, SSR
├─────────────────┤
│   Data Layer    │ ← Models, migrations, auto APIs
├─────────────────┤
│   Plugins       │ ← Auth, cache, analytics, etc.
├─────────────────┤
│   Server        │ ← Context detection, adaptive rendering
└─────────────────┘
```

This example demonstrates how all these layers work together to create a modern, full-featured web application with minimal boilerplate code.

## Next Steps

- Explore the code in `main.py` to see how each feature is implemented
- Try modifying components to see hot reload in action
- Add new models and see the APIs automatically generated
- Customize the styling and see adaptive rendering at work
- Check the browser developer tools to see the compiled JavaScript

The entire application is less than 500 lines of Python code, yet includes features that would typically require multiple frameworks, build tools, and thousands of lines of configuration!
