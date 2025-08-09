# Routing and Navigation

PyFrame's routing system provides flexible URL handling and seamless navigation for your web applications. This guide covers everything from basic routes to advanced navigation patterns.

## 🛣️ Route Basics

### Route Types

PyFrame supports multiple routing patterns:

1. **Static Routes**: Fixed URL paths
2. **Dynamic Routes**: URL parameters and wildcards  
3. **Component Routes**: Direct component rendering
4. **API Routes**: JSON endpoints
5. **WebSocket Routes**: Real-time connections

## 🎯 Static Routes

Static routes handle fixed URL paths.

```python
from pyframe import PyFrameApp

app = PyFrameApp()

@app.route('/')
async def home(context):
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': '<h1>Welcome to PyFrame!</h1>'
    }

@app.route('/about')
async def about(context):
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': '<h1>About Us</h1><p>We build amazing things with PyFrame.</p>'
    }

@app.route('/contact')
async def contact(context):
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': '''
        <h1>Contact Us</h1>
        <form action="/contact" method="POST">
            <input name="email" placeholder="Your email" required>
            <textarea name="message" placeholder="Your message" required></textarea>
            <button type="submit">Send</button>
        </form>
        '''
    }
```

## 🔀 Dynamic Routes

Dynamic routes use URL parameters to handle variable paths.

### URL Parameters

```python
# Single parameter
@app.route('/user/<user_id>')
async def user_profile(context):
    user_id = context.params['user_id']
    user = await User.get(user_id)
    
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f'<h1>Profile for {user.name}</h1>'
    }

# Multiple parameters
@app.route('/blog/<year>/<month>/<slug>')
async def blog_post(context):
    year = context.params['year']
    month = context.params['month']
    slug = context.params['slug']
    
    post = await BlogPost.filter(
        created_at__year=year,
        created_at__month=month,
        slug=slug
    ).first()
    
    if not post:
        return {'status': 404, 'body': 'Post not found'}
    
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f'''
        <article>
            <h1>{post.title}</h1>
            <time>{post.created_at}</time>
            <div>{post.content}</div>
        </article>
        '''
    }
```

### Type Conversion

```python
# Integer parameters
@app.route('/post/<int:post_id>')
async def post_detail(context):
    post_id = context.params['post_id']  # Automatically converted to int
    post = await Post.get(post_id)
    return {'status': 200, 'body': f'Post {post_id}: {post.title}'}

# Float parameters
@app.route('/product/<float:price>/discount')
async def price_discount(context):
    price = context.params['price']  # Automatically converted to float
    discounted = price * 0.9
    return {'status': 200, 'body': f'Discounted price: ${discounted:.2f}'}

# UUID parameters
@app.route('/order/<uuid:order_id>')
async def order_status(context):
    order_id = context.params['order_id']  # Automatically converted to UUID
    order = await Order.get(order_id)
    return {'status': 200, 'body': f'Order status: {order.status}'}
```

### Wildcard Routes

```python
# Catch-all route
@app.route('/files/<path:filename>')
async def serve_file(context):
    filename = context.params['filename']  # Can contain slashes
    
    # Security check
    if '..' in filename or filename.startswith('/'):
        return {'status': 403, 'body': 'Forbidden'}
    
    file_path = f'static/{filename}'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        
        content_type = guess_content_type(filename)
        return {
            'status': 200,
            'headers': {'Content-Type': content_type},
            'body': content
        }
    
    return {'status': 404, 'body': 'File not found'}
```

## 🧩 Component Routes

Component routes directly render PyFrame components.

```python
from pyframe import Component, StatefulComponent

class HomePage(Component):
    def render(self):
        return '''
        <div class="home">
            <h1>Welcome to PyFrame</h1>
            <p>Build amazing apps with Python!</p>
        </div>
        '''

class Dashboard(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'user': None,
            'stats': {}
        })
    
    async def component_did_mount(self):
        user = await self.load_user()
        stats = await self.load_stats()
        self.state.update('user', user)
        self.state.update('stats', stats)
    
    def render(self):
        user = self.state.get('user')
        stats = self.state.get('stats')
        
        return f'''
        <div class="dashboard">
            <h1>Welcome back, {user.name if user else 'User'}!</h1>
            <div class="stats">
                <div class="stat">
                    <h3>Total Sales</h3>
                    <p>${stats.get('total_sales', 0)}</p>
                </div>
                <div class="stat">
                    <h3>New Users</h3>
                    <p>{stats.get('new_users', 0)}</p>
                </div>
            </div>
        </div>
        '''

# Register component routes
@app.component_route('/')
class HomeRoute(HomePage):
    pass

@app.component_route('/dashboard')
class DashboardRoute(Dashboard):
    pass

# With parameters
@app.component_route('/profile/<user_id>')
class ProfileRoute(UserProfile):
    def __init__(self, **props):
        user_id = props.get('user_id')
        super().__init__(user_id=user_id, **props)
```

## 🔌 API Routes

Create JSON APIs with automatic serialization.

```python
from pyframe.decorators import api_route, cors

# Simple API endpoint
@app.api_route('/api/users')
async def list_users(context):
    users = await User.all()
    return {
        'users': [user.to_dict() for user in users],
        'total': len(users)
    }

# API with CORS
@app.api_route('/api/products')
@cors(origins=['https://example.com'], methods=['GET', 'POST'])
async def products_api(context):
    if context.method == 'GET':
        products = await Product.all()
        return {'products': [p.to_dict() for p in products]}
    
    elif context.method == 'POST':
        data = await context.json()
        product = await Product.create(**data)
        return {'product': product.to_dict()}, 201

# API with authentication
@app.api_route('/api/protected')
@auth_required
async def protected_api(context):
    user = context.user
    return {'message': f'Hello {user.name}', 'user_id': user.id}
```

## 🌐 WebSocket Routes

Handle real-time connections with WebSocket routes.

```python
from pyframe.realtime import WebSocketManager

ws_manager = WebSocketManager()

@app.websocket('/ws/chat')
async def chat_handler(websocket):
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Broadcast to all connected clients
            await ws_manager.broadcast({
                'type': 'message',
                'user': data['user'],
                'text': data['text'],
                'timestamp': datetime.now().isoformat()
            })
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)

@app.websocket('/ws/notifications/<user_id>')
async def user_notifications(websocket, user_id):
    await ws_manager.connect(websocket, group=f"user_{user_id}")
    
    try:
        # Send pending notifications
        notifications = await Notification.filter(user_id=user_id, read=False)
        for notification in notifications:
            await websocket.send_json({
                'type': 'notification',
                'data': notification.to_dict()
            })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    
    except:
        pass
    finally:
        await ws_manager.disconnect(websocket)
```

## 🧭 Navigation and Redirects

### Redirects

```python
from pyframe.responses import redirect

@app.route('/old-page')
async def old_page(context):
    return redirect('/new-page', permanent=True)

@app.route('/login')
async def login_redirect(context):
    if context.user:
        return redirect('/dashboard')
    
    return {
        'status': 200,
        'body': render_login_form()
    }

# Conditional redirects
@app.route('/admin')
async def admin_area(context):
    if not context.user:
        return redirect('/login?next=/admin')
    
    if not context.user.is_admin:
        return redirect('/dashboard')
    
    return AdminDashboard().render()
```

### URL Generation

```python
from pyframe.urls import reverse

# Generate URLs in templates
@app.route('/products')
async def product_list(context):
    products = await Product.all()
    
    html = '<h1>Products</h1><ul>'
    for product in products:
        product_url = reverse('product_detail', product_id=product.id)
        html += f'<li><a href="{product_url}">{product.name}</a></li>'
    html += '</ul>'
    
    return {'status': 200, 'body': html}

# Named routes
@app.route('/product/<int:product_id>', name='product_detail')
async def product_detail(context):
    product_id = context.params['product_id']
    product = await Product.get(product_id)
    
    edit_url = reverse('product_edit', product_id=product.id)
    
    return {
        'status': 200,
        'body': f'''
        <h1>{product.name}</h1>
        <p>{product.description}</p>
        <a href="{edit_url}">Edit Product</a>
        '''
    }
```

## 🔒 Route Protection

### Authentication Middleware

```python
from functools import wraps

def auth_required(func):
    @wraps(func)
    async def wrapper(context):
        if not context.user:
            return redirect('/login')
        return await func(context)
    return wrapper

def admin_required(func):
    @wraps(func)
    async def wrapper(context):
        if not context.user or not context.user.is_admin:
            return {'status': 403, 'body': 'Forbidden'}
        return await func(context)
    return wrapper

# Protected routes
@app.route('/profile')
@auth_required
async def profile(context):
    user = context.user
    return UserProfile(user=user).render()

@app.route('/admin/users')
@admin_required
async def admin_users(context):
    users = await User.all()
    return AdminUserList(users=users).render()
```

### Permission-Based Access

```python
from pyframe.auth import has_permission

@app.route('/posts/<int:post_id>/edit')
@auth_required
async def edit_post(context):
    post_id = context.params['post_id']
    post = await Post.get(post_id)
    
    # Check if user can edit this post
    if not has_permission(context.user, 'edit_post', post):
        return {'status': 403, 'body': 'You cannot edit this post'}
    
    return PostEditor(post=post).render()
```

## ⚡ Route Groups and Prefixes

### Route Groups

```python
# API routes group
@app.route_group('/api/v1')
class APIRoutes:
    @app.route('/users')
    async def users(self, context):
        return {'users': await User.all()}
    
    @app.route('/posts')
    async def posts(self, context):
        return {'posts': await Post.all()}

# Admin routes group
@app.route_group('/admin')
@admin_required
class AdminRoutes:
    @app.route('/dashboard')
    async def dashboard(self, context):
        return AdminDashboard().render()
    
    @app.route('/users')
    async def users(self, context):
        return AdminUserManager().render()
```

### Middleware for Route Groups

```python
@app.middleware_group('/api')
class APIMiddleware:
    async def before_request(self, context):
        # Add CORS headers
        context.response_headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        })
    
    async def after_request(self, context, response):
        # Add API response timing
        response['headers']['X-Response-Time'] = str(context.processing_time)
        return response
```

## 🔧 Advanced Routing

### Route Conditions

```python
# Host-based routing
@app.route('/admin', host='admin.example.com')
async def admin_portal(context):
    return AdminPortal().render()

# Method-specific routes
@app.route('/api/users', methods=['GET'])
async def get_users(context):
    return {'users': await User.all()}

@app.route('/api/users', methods=['POST'])
async def create_user(context):
    data = await context.json()
    user = await User.create(**data)
    return {'user': user.to_dict()}, 201

# Custom route conditions
@app.route('/mobile-app', condition=lambda ctx: ctx.is_mobile)
async def mobile_app(context):
    return MobileApp().render()
```

### Route Priority

```python
# Specific routes should come before general ones
@app.route('/users/new')  # Specific
async def new_user(context):
    return NewUserForm().render()

@app.route('/users/<user_id>')  # General
async def user_detail(context):
    user_id = context.params['user_id']
    return UserDetail(user_id=user_id).render()
```

## 📱 Client-Side Navigation

### Single Page Application (SPA) Support

```python
@app.route('/<path:path>')
async def spa_handler(context):
    # Serve the main SPA template for all routes
    # Let client-side routing handle the rest
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyFrame SPA</title>
            <script src="/static/pyframe-spa.js"></script>
        </head>
        <body>
            <div id="app"></div>
        </body>
        </html>
        '''
    }

# API routes for SPA
@app.api_route('/api/pages/<path>')
async def spa_api(context):
    path = context.params['path']
    
    # Return page data for client-side rendering
    if path == 'home':
        return {'component': 'HomePage', 'props': {}}
    elif path.startswith('user/'):
        user_id = path.split('/')[1]
        user = await User.get(user_id)
        return {'component': 'UserProfile', 'props': {'user': user.to_dict()}}
    
    return {'component': 'NotFound', 'props': {}}, 404
```

## 📚 Best Practices

### 1. Organize Routes Logically
```python
# Group related routes together
# auth.py
@app.route('/login')
@app.route('/logout')
@app.route('/register')

# blog.py  
@app.route('/blog')
@app.route('/blog/<slug>')
@app.route('/blog/category/<category>')

# api.py
@app.api_route('/api/auth')
@app.api_route('/api/users')
@app.api_route('/api/posts')
```

### 2. Use Descriptive Route Names
```python
@app.route('/user/<int:user_id>/posts', name='user_posts')
@app.route('/post/<int:post_id>/edit', name='edit_post')
@app.route('/admin/users', name='admin_user_list')
```

### 3. Handle Errors Gracefully
```python
@app.route('/user/<int:user_id>')
async def user_profile(context):
    try:
        user = await User.get(context.params['user_id'])
        return UserProfile(user=user).render()
    except User.DoesNotExist:
        return {'status': 404, 'body': 'User not found'}
    except Exception as e:
        return {'status': 500, 'body': f'Server error: {e}'}
```

## 📚 Next Steps

- [Data Models and APIs](data-models-apis.md)
- [Real-Time Features](realtime-features.md)
- [Advanced Topics](advanced-topics.md)
- [Server API Reference](api-reference/server-api.md)

Master PyFrame's routing system and you'll be able to build complex, well-organized web applications with ease! 🚀
