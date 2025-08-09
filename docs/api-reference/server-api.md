# Server API Reference

Complete reference for PyFrame's server and request handling APIs.

## Development Server

### `SimpleDevServer`

PyFrame's built-in development server with hot reload capabilities.

```python
from pyframe.server import SimpleDevServer

server = SimpleDevServer(
    app=app,
    host='localhost',
    port=3000,
    hot_reload=True
)
await server.start()
```

#### Constructor Parameters

##### `app: PyFrameApp`
The PyFrame application instance to serve.

##### `host: str`
Server host address. Default: `'localhost'`

##### `port: int`
Server port number. Default: `3000`

##### `hot_reload: bool`
Enable hot reload functionality. Default: `True`

##### `debug: bool`
Enable debug mode. Default: `True`

##### `static_path: str`
Path to static files directory. Default: `'static'`

#### Methods

##### `async start()`
Start the development server.

**Example:**
```python
server = SimpleDevServer(app)
await server.start()
```

##### `async stop()`
Stop the development server.

##### `async restart()`
Restart the server (useful for hot reload).

##### `get_status() -> dict`
Get server status information.

**Returns:**
- `dict` - Server status including uptime, request count, etc.

---

## Request Context

### `RequestContext`

Contains information about the current HTTP request.

```python
@app.route('/users/<user_id>')
async def get_user(context):
    user_id = context.params['user_id']
    query = context.query_params.get('include')
    return {'user_id': user_id, 'include': query}
```

#### Attributes

##### `method: str`
HTTP method (GET, POST, PUT, DELETE, etc.).

##### `path: str`
Request path without query parameters.

##### `full_path: str`
Full request path including query parameters.

##### `params: dict`
URL path parameters from route patterns.

##### `query_params: dict`
Query string parameters.

##### `headers: dict`
Request headers.

##### `cookies: dict`
Request cookies.

##### `json: dict`
Parsed JSON body (for POST/PUT requests).

##### `form: dict`
Parsed form data.

##### `files: dict`
Uploaded files.

##### `raw_body: bytes`
Raw request body.

##### `user: User`
Authenticated user (if available).

##### `session: dict`
User session data.

##### `remote_addr: str`
Client IP address.

##### `user_agent: str`
Client user agent string.

#### Methods

##### `get_header(self, name, default=None) -> str`
Get request header value.

**Parameters:**
- `name: str` - Header name (case-insensitive)
- `default: Any` - Default value if header not found

**Returns:**
- `str` - Header value or default

**Example:**
```python
content_type = context.get_header('Content-Type', 'text/html')
auth_header = context.get_header('Authorization')
```

##### `get_cookie(self, name, default=None) -> str`
Get cookie value.

**Parameters:**
- `name: str` - Cookie name
- `default: Any` - Default value if cookie not found

**Returns:**
- `str` - Cookie value or default

##### `get_query_param(self, name, default=None) -> str`
Get query parameter value.

**Parameters:**
- `name: str` - Parameter name
- `default: Any` - Default value if parameter not found

**Returns:**
- `str` - Parameter value or default

##### `is_ajax(self) -> bool`
Check if request is an AJAX request.

**Returns:**
- `bool` - True if AJAX request

##### `is_json(self) -> bool`
Check if request content type is JSON.

**Returns:**
- `bool` - True if JSON content type

##### `accepts(self, content_type) -> bool`
Check if client accepts specific content type.

**Parameters:**
- `content_type: str` - MIME type to check

**Returns:**
- `bool` - True if content type is accepted

**Example:**
```python
if context.accepts('application/json'):
    return {'data': 'json response'}
else:
    return {'body': '<html>HTML response</html>'}
```

---

## Response Builder

### Creating Responses

#### Basic Response

```python
@app.route('/hello')
async def hello(context):
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'Hello, World!'
    }
```

#### JSON Response

```python
@app.route('/api/users')
async def get_users(context):
    users = await User.all()
    return {
        'status': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps([user.to_dict() for user in users])
    }
```

#### HTML Response

```python
@app.route('/dashboard')
async def dashboard(context):
    dashboard_component = Dashboard(user=context.user)
    return {
        'status': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': dashboard_component.render()
    }
```

#### Redirect Response

```python
@app.route('/old-path')
async def redirect_old_path(context):
    return {
        'status': 302,
        'headers': {'Location': '/new-path'}
    }
```

#### File Response

```python
@app.route('/download/<filename>')
async def download_file(context):
    filename = context.params['filename']
    file_path = f'/uploads/{filename}'
    
    if not os.path.exists(file_path):
        return {'status': 404, 'body': 'File not found'}
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    return {
        'status': 200,
        'headers': {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(content))
        },
        'body': content
    }
```

### Response Helpers

```python
from pyframe.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse

@app.route('/api/data')
async def api_data(context):
    data = {'message': 'Hello, API!'}
    return JSONResponse(data, status=200)

@app.route('/page')
async def page(context):
    html = '<h1>Welcome</h1>'
    return HTMLResponse(html)

@app.route('/redirect')
async def redirect(context):
    return RedirectResponse('/destination', status=302)

@app.route('/file')
async def serve_file(context):
    return FileResponse('/path/to/file.pdf', filename='download.pdf')
```

---

## Middleware System

### Middleware Interface

```python
async def my_middleware(context, call_next):
    """Custom middleware function"""
    
    # Pre-processing
    start_time = time.time()
    print(f"Request started: {context.path}")
    
    # Call next middleware/handler
    response = await call_next(context)
    
    # Post-processing
    duration = time.time() - start_time
    print(f"Request completed in {duration:.3f}s")
    
    # Modify response
    response.setdefault('headers', {})
    response['headers']['X-Response-Time'] = f"{duration:.3f}s"
    
    return response

# Register middleware
app.middleware.append(my_middleware)
```

### Built-in Middleware

#### CORS Middleware

```python
from pyframe.middleware import CORSMiddleware

cors_middleware = CORSMiddleware(
    allow_origins=['*'],
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*'],
    allow_credentials=True
)

app.middleware.append(cors_middleware)
```

#### Authentication Middleware

```python
from pyframe.middleware import AuthMiddleware

auth_middleware = AuthMiddleware(
    secret_key='your-secret-key',
    exclude_paths=['/login', '/register', '/public']
)

app.middleware.append(auth_middleware)
```

#### Rate Limiting Middleware

```python
from pyframe.middleware import RateLimitMiddleware

rate_limit_middleware = RateLimitMiddleware(
    requests_per_minute=60,
    burst_size=10
)

app.middleware.append(rate_limit_middleware)
```

#### Compression Middleware

```python
from pyframe.middleware import CompressionMiddleware

compression_middleware = CompressionMiddleware(
    minimum_size=1024,  # Only compress responses larger than 1KB
    compression_level=6
)

app.middleware.append(compression_middleware)
```

### Custom Middleware Examples

#### Request ID Middleware

```python
import uuid

async def request_id_middleware(context, call_next):
    """Add unique request ID to each request"""
    request_id = str(uuid.uuid4())
    context.request_id = request_id
    
    response = await call_next(context)
    
    response.setdefault('headers', {})
    response['headers']['X-Request-ID'] = request_id
    
    return response
```

#### Security Headers Middleware

```python
async def security_headers_middleware(context, call_next):
    """Add security headers to responses"""
    response = await call_next(context)
    
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'"
    }
    
    response.setdefault('headers', {})
    response['headers'].update(security_headers)
    
    return response
```

#### Error Handling Middleware

```python
import traceback

async def error_handling_middleware(context, call_next):
    """Global error handling"""
    try:
        return await call_next(context)
    
    except ValueError as e:
        return {
            'status': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bad Request', 'message': str(e)})
        }
    
    except PermissionError as e:
        return {
            'status': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Forbidden', 'message': str(e)})
        }
    
    except Exception as e:
        # Log error
        print(f"Unhandled error: {e}")
        print(traceback.format_exc())
        
        if context.app.debug:
            return {
                'status': 500,
                'headers': {'Content-Type': 'text/plain'},
                'body': traceback.format_exc()
            }
        else:
            return {
                'status': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Internal Server Error'})
            }
```

---

## WebSocket Support

### WebSocket Handler

```python
from pyframe.websockets import WebSocketManager

ws_manager = WebSocketManager()

@app.websocket('/ws/chat')
async def chat_websocket(websocket):
    """WebSocket endpoint for chat"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive message
            message = await websocket.receive_json()
            
            # Process message
            processed_message = {
                'user': message['user'],
                'text': message['text'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast to all connected clients
            await ws_manager.broadcast(processed_message)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)
```

### WebSocket Manager API

#### `WebSocketManager`

Manages WebSocket connections and messaging.

##### Methods

###### `async connect(websocket)`
Register a new WebSocket connection.

###### `async disconnect(websocket)`
Remove a WebSocket connection.

###### `async broadcast(message)`
Send message to all connected clients.

###### `async send_to_user(user_id, message)`
Send message to specific user.

###### `async join_group(websocket, group_name)`
Add connection to a group.

###### `async leave_group(websocket, group_name)`
Remove connection from a group.

###### `async broadcast_to_group(group_name, message)`
Send message to all connections in a group.

###### `get_connection_count() -> int`
Get total number of active connections.

###### `get_group_size(group_name) -> int`
Get number of connections in a group.

---

## Server-Sent Events

### SSE Handler

```python
from pyframe.sse import SSEManager

sse_manager = SSEManager()

@app.route('/events')
async def event_stream(context):
    """Server-Sent Events endpoint"""
    
    async def event_generator():
        # Send initial connection event
        yield {
            'event': 'connected',
            'data': {'timestamp': datetime.now().isoformat()}
        }
        
        # Subscribe to events for this user
        user_id = context.user.id if context.user else 'anonymous'
        
        async for event in sse_manager.subscribe(f"user_{user_id}"):
            yield event
    
    return {
        'status': 200,
        'headers': {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        },
        'body': event_generator()
    }

# Send events from other parts of your application
await sse_manager.send_event('user_123', {
    'event': 'notification',
    'data': {'message': 'You have a new message'}
})
```

---

## Static File Serving

### Static File Configuration

```python
# Serve static files from 'static' directory at '/static/' URL
app.add_static_path('/static/', 'static/')

# Serve uploaded files
app.add_static_path('/uploads/', '/var/uploads/')

# Serve with custom headers
app.add_static_path('/assets/', 'assets/', headers={
    'Cache-Control': 'public, max-age=31536000'
})
```

### Custom Static File Handler

```python
import mimetypes
import os
from pathlib import Path

async def custom_static_handler(context):
    """Custom static file handler with optimization"""
    
    # Get requested file path
    file_path = context.params.get('file_path', '')
    full_path = Path('static') / file_path
    
    # Security check - prevent directory traversal
    if not str(full_path.resolve()).startswith(str(Path('static').resolve())):
        return {'status': 403, 'body': 'Forbidden'}
    
    # Check if file exists
    if not full_path.exists() or not full_path.is_file():
        return {'status': 404, 'body': 'Not Found'}
    
    # Get file info
    file_stat = full_path.stat()
    file_size = file_stat.st_size
    file_mtime = file_stat.st_mtime
    
    # Check If-Modified-Since header
    if_modified_since = context.get_header('If-Modified-Since')
    if if_modified_since:
        # Compare with file modification time
        # Return 304 if not modified
        pass
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(full_path))
    content_type = content_type or 'application/octet-stream'
    
    # Read file content
    with open(full_path, 'rb') as f:
        content = f.read()
    
    # Prepare response headers
    headers = {
        'Content-Type': content_type,
        'Content-Length': str(file_size),
        'Last-Modified': datetime.fromtimestamp(file_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'Cache-Control': 'public, max-age=3600'
    }
    
    return {
        'status': 200,
        'headers': headers,
        'body': content
    }

# Register custom static handler
app.route('/custom-static/<path:file_path>')(custom_static_handler)
```

---

## Performance Monitoring

### Server Metrics

```python
class ServerMetrics:
    """Collect server performance metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.total_response_time = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def record_request(self, response_time, status_code):
        """Record request metrics"""
        self.request_count += 1
        self.total_response_time += response_time
        
        if status_code >= 400:
            self.error_count += 1
    
    def get_stats(self):
        """Get current server statistics"""
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            'uptime_seconds': uptime,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / self.request_count if self.request_count > 0 else 0,
            'avg_response_time': avg_response_time,
            'requests_per_second': self.request_count / uptime if uptime > 0 else 0
        }

# Global metrics instance
server_metrics = ServerMetrics()

# Metrics middleware
async def metrics_middleware(context, call_next):
    start_time = time.time()
    
    response = await call_next(context)
    
    response_time = time.time() - start_time
    status_code = response.get('status', 200)
    
    server_metrics.record_request(response_time, status_code)
    
    return response

# Metrics endpoint
@app.route('/admin/metrics')
async def get_metrics(context):
    stats = server_metrics.get_stats()
    return {
        'status': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(stats)
    }
```

This completes the Server API reference. PyFrame provides a powerful and flexible server system for building modern web applications! 🚀
