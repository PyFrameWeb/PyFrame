# Real-Time Features

PyFrame provides built-in real-time capabilities through WebSockets, Server-Sent Events (SSE), and live data synchronization, making it easy to build interactive, collaborative applications.

## 🌐 WebSocket Integration

### Basic WebSocket Setup

```python
from pyframe import PyFrameApp
from pyframe.realtime import WebSocketManager

app = PyFrameApp()
ws_manager = WebSocketManager()

@app.websocket('/ws/chat')
async def chat_handler(websocket):
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message
            message = {
                'user': data['user'],
                'text': data['text'],
                'timestamp': datetime.now().isoformat(),
                'type': 'message'
            }
            
            # Broadcast to all connected clients
            await ws_manager.broadcast(message)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)
```

### WebSocket with User Groups

```python
@app.websocket('/ws/room/<room_id>')
async def room_handler(websocket, room_id):
    user_id = await authenticate_websocket(websocket)
    if not user_id:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    # Join room-specific group
    await ws_manager.join_group(websocket, f"room_{room_id}")
    
    try:
        # Send room history to new user
        history = await get_room_history(room_id)
        await websocket.send_json({
            'type': 'history',
            'messages': history
        })
        
        # Notify others that user joined
        await ws_manager.broadcast_to_group(f"room_{room_id}", {
            'type': 'user_joined',
            'user_id': user_id,
            'message': f"User {user_id} joined the room"
        }, exclude=websocket)
        
        while True:
            data = await websocket.receive_json()
            
            # Save message to database
            message = await save_message(room_id, user_id, data['text'])
            
            # Broadcast to room members
            await ws_manager.broadcast_to_group(f"room_{room_id}", {
                'type': 'message',
                'id': message.id,
                'user_id': user_id,
                'text': data['text'],
                'timestamp': message.created_at.isoformat()
            })
    
    except Exception as e:
        print(f"Room WebSocket error: {e}")
    finally:
        await ws_manager.leave_group(websocket, f"room_{room_id}")
        await ws_manager.broadcast_to_group(f"room_{room_id}", {
            'type': 'user_left',
            'user_id': user_id,
            'message': f"User {user_id} left the room"
        })
```

## 📡 Server-Sent Events (SSE)

### Basic SSE Implementation

```python
from pyframe.realtime import SSEManager

sse_manager = SSEManager()

@app.route('/events')
async def event_stream(context):
    user_id = context.user.id
    
    # Create SSE response
    async def event_generator():
        # Send initial connection event
        yield {
            'event': 'connected',
            'data': {'user_id': user_id, 'timestamp': datetime.now().isoformat()}
        }
        
        # Subscribe to user-specific events
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

# Send events from elsewhere in your application
async def notify_user(user_id, event_type, data):
    await sse_manager.send_event(f"user_{user_id}", {
        'event': event_type,
        'data': data
    })

# Example: Notify user of new message
await notify_user(123, 'new_message', {
    'message_id': 456,
    'sender': 'Alice',
    'preview': 'Hello there!'
})
```

### SSE with Filtering

```python
@app.route('/events/notifications')
async def notification_stream(context):
    user_id = context.user.id
    
    async def filtered_events():
        async for event in sse_manager.subscribe(f"notifications_{user_id}"):
            # Filter events based on user preferences
            if should_send_notification(user_id, event):
                yield {
                    'event': 'notification',
                    'data': event['data'],
                    'id': event.get('id', str(uuid.uuid4()))
                }
    
    return {
        'status': 200,
        'headers': {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        },
        'body': filtered_events()
    }
```

## 🔄 Live Data Synchronization

### Database Change Streaming

```python
from pyframe.realtime import LiveSync
from pyframe import Model, Field, FieldType

class Post(Model):
    title = Field(FieldType.STRING, max_length=200)
    content = Field(FieldType.TEXT)
    author_id = Field(FieldType.INTEGER)
    published = Field(FieldType.BOOLEAN, default=False)

# Set up live sync
live_sync = LiveSync()

# Sync model changes to WebSocket clients
@live_sync.watch(Post)
async def sync_post_changes(action, instance, old_instance=None):
    """Automatically sync post changes to connected clients"""
    
    event_data = {
        'model': 'Post',
        'action': action,  # 'created', 'updated', 'deleted'
        'instance': instance.to_dict() if instance else None,
        'old_instance': old_instance.to_dict() if old_instance else None
    }
    
    if action == 'created':
        # Notify all users of new post
        await ws_manager.broadcast({
            'type': 'post_created',
            'post': instance.to_dict()
        })
    
    elif action == 'updated':
        # Notify users following this post
        followers = await get_post_followers(instance.id)
        for follower_id in followers:
            await ws_manager.send_to_user(follower_id, {
                'type': 'post_updated',
                'post': instance.to_dict(),
                'changes': get_changes(old_instance, instance)
            })
    
    elif action == 'deleted':
        # Notify all clients of deletion
        await ws_manager.broadcast({
            'type': 'post_deleted',
            'post_id': old_instance.id
        })

# Enable live sync
live_sync.start()
```

### Real-Time Component Updates

```python
from pyframe import StatefulComponent
from pyframe.realtime import LiveComponent

class LivePostList(LiveComponent):
    """Component that automatically updates when posts change"""
    
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'posts': [],
            'loading': True,
            'connected': False
        })
    
    async def component_did_mount(self):
        # Load initial data
        posts = await Post.filter(published=True).order_by('-created_at')
        self.state.set_multiple({
            'posts': [p.to_dict() for p in posts],
            'loading': False
        })
        
        # Connect to live updates
        await self.connect_live_updates()
    
    async def connect_live_updates(self):
        """Connect to WebSocket for live updates"""
        await self.ws_connect('/ws/posts')
        self.state.update('connected', True)
    
    async def handle_ws_message(self, message):
        """Handle incoming WebSocket messages"""
        if message['type'] == 'post_created':
            posts = self.state.get('posts')
            posts.insert(0, message['post'])
            self.state.update('posts', posts)
            
        elif message['type'] == 'post_updated':
            posts = self.state.get('posts')
            for i, post in enumerate(posts):
                if post['id'] == message['post']['id']:
                    posts[i] = message['post']
                    break
            self.state.update('posts', posts)
            
        elif message['type'] == 'post_deleted':
            posts = self.state.get('posts')
            posts = [p for p in posts if p['id'] != message['post_id']]
            self.state.update('posts', posts)
    
    def render(self):
        posts = self.state.get('posts')
        loading = self.state.get('loading')
        connected = self.state.get('connected')
        
        if loading:
            return '<div class="loading">Loading posts...</div>'
        
        status_indicator = '🟢' if connected else '🔴'
        
        posts_html = ''.join([
            f'''
            <article class="post" data-id="{post['id']}">
                <h3>{post['title']}</h3>
                <p>{post['content'][:100]}...</p>
                <small>By {post['author_name']} • {post['created_at']}</small>
            </article>
            '''
            for post in posts
        ])
        
        return f'''
        <div class="live-post-list">
            <div class="status">
                {status_indicator} Live Updates
            </div>
            <div class="posts">
                {posts_html or '<p>No posts yet.</p>'}
            </div>
        </div>
        '''
```

## 🎯 Collaborative Features

### Real-Time Collaborative Editing

```python
from pyframe.realtime import CollaborativeDocument

class DocumentEditor(StatefulComponent):
    """Real-time collaborative document editor"""
    
    def __init__(self, document_id, **props):
        super().__init__(**props)
        self.document_id = document_id
        self.state = State({
            'content': '',
            'cursors': {},
            'users': [],
            'saving': False
        })
        
        self.collab_doc = CollaborativeDocument(document_id)
    
    async def component_did_mount(self):
        # Load document content
        doc = await Document.get(self.document_id)
        self.state.update('content', doc.content)
        
        # Join collaborative session
        await self.collab_doc.join(self.handle_doc_changes)
        
        # Load current users
        users = await self.collab_doc.get_active_users()
        self.state.update('users', users)
    
    async def handle_doc_changes(self, changes):
        """Handle incoming collaborative changes"""
        if changes['type'] == 'content_change':
            # Apply operational transformation
            new_content = self.apply_ot_changes(
                self.state.get('content'),
                changes['operations']
            )
            self.state.update('content', new_content)
            
        elif changes['type'] == 'cursor_update':
            cursors = self.state.get('cursors')
            cursors[changes['user_id']] = changes['position']
            self.state.update('cursors', cursors)
            
        elif changes['type'] == 'user_joined':
            users = self.state.get('users')
            users.append(changes['user'])
            self.state.update('users', users)
            
        elif changes['type'] == 'user_left':
            users = self.state.get('users')
            users = [u for u in users if u['id'] != changes['user_id']]
            self.state.update('users', users)
            
            # Remove user's cursor
            cursors = self.state.get('cursors')
            cursors.pop(changes['user_id'], None)
            self.state.update('cursors', cursors)
    
    async def handle_text_change(self, new_content, cursor_position):
        """Handle local text changes"""
        old_content = self.state.get('content')
        
        # Generate operational transformation operations
        operations = self.generate_ot_operations(old_content, new_content)
        
        # Send changes to other users
        await self.collab_doc.send_changes({
            'type': 'content_change',
            'operations': operations,
            'cursor_position': cursor_position
        })
        
        # Update local state
        self.state.update('content', new_content)
        
        # Auto-save after delay
        self.schedule_save()
    
    def schedule_save(self):
        """Schedule document save with debouncing"""
        if hasattr(self, 'save_timer'):
            self.save_timer.cancel()
        
        self.save_timer = asyncio.create_task(self.auto_save())
    
    async def auto_save(self):
        """Auto-save document after delay"""
        await asyncio.sleep(2)  # 2 second delay
        
        self.state.update('saving', True)
        try:
            await Document.filter(id=self.document_id).update(
                content=self.state.get('content'),
                updated_at=datetime.now()
            )
        finally:
            self.state.update('saving', False)
    
    def render(self):
        content = self.state.get('content')
        users = self.state.get('users')
        cursors = self.state.get('cursors')
        saving = self.state.get('saving')
        
        # Render user avatars
        user_avatars = ''.join([
            f'<img src="{user["avatar"]}" alt="{user["name"]}" title="{user["name"]}">'
            for user in users
        ])
        
        # Render cursor indicators
        cursor_indicators = ''.join([
            f'<span class="cursor" style="left: {pos}px;" data-user="{user_id}"></span>'
            for user_id, pos in cursors.items()
        ])
        
        save_indicator = '💾 Saving...' if saving else '✅ Saved'
        
        return f'''
        <div class="document-editor">
            <div class="toolbar">
                <div class="users">
                    {user_avatars}
                    <span class="user-count">{len(users)} online</span>
                </div>
                <div class="save-status">{save_indicator}</div>
            </div>
            
            <div class="editor-container">
                <textarea
                    class="editor"
                    value="{content}"
                    oninput="this.component.handle_text_change(this.value, this.selectionStart)"
                    onselectionchange="this.component.handle_cursor_move(this.selectionStart)"
                ></textarea>
                {cursor_indicators}
            </div>
        </div>
        '''
```

### Real-Time Notifications

```python
from pyframe.realtime import NotificationManager

notification_manager = NotificationManager()

class NotificationSystem(StatefulComponent):
    """Real-time notification system"""
    
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'notifications': [],
            'unread_count': 0,
            'show_panel': False
        })
    
    async def component_did_mount(self):
        # Load existing notifications
        notifications = await Notification.filter(
            user_id=self.context.user.id,
            created_at__gte=datetime.now() - timedelta(days=7)
        ).order_by('-created_at')
        
        self.state.set_multiple({
            'notifications': [n.to_dict() for n in notifications],
            'unread_count': len([n for n in notifications if not n.read])
        })
        
        # Connect to real-time notifications
        await self.connect_notifications()
    
    async def connect_notifications(self):
        """Connect to notification stream"""
        user_id = self.context.user.id
        
        async def handle_notification(notification):
            notifications = self.state.get('notifications')
            notifications.insert(0, notification)
            
            # Keep only recent notifications
            notifications = notifications[:50]
            
            unread_count = self.state.get('unread_count')
            if not notification['read']:
                unread_count += 1
            
            self.state.set_multiple({
                'notifications': notifications,
                'unread_count': unread_count
            })
            
            # Show browser notification if permission granted
            self.show_browser_notification(notification)
        
        await notification_manager.subscribe(f"user_{user_id}", handle_notification)
    
    def show_browser_notification(self, notification):
        """Show browser notification"""
        self.execute_js(f'''
            if (Notification.permission === "granted") {% raw %}{{{% endraw %}
                new Notification("{notification['title']}", {% raw %}{{{% endraw %}
                    body: "{notification['message']}",
                    icon: "/static/notification-icon.png"
                {% raw %}}}{% endraw %});
            {% raw %}}}{% endraw %}
        ''')
    
    async def mark_as_read(self, notification_id):
        """Mark notification as read"""
        await Notification.filter(id=notification_id).update(read=True)
        
        notifications = self.state.get('notifications')
        for notification in notifications:
            if notification['id'] == notification_id:
                notification['read'] = True
                break
        
        unread_count = self.state.get('unread_count')
        self.state.set_multiple({
            'notifications': notifications,
            'unread_count': max(0, unread_count - 1)
        })
    
    def toggle_panel(self):
        """Toggle notification panel"""
        show_panel = not self.state.get('show_panel')
        self.state.update('show_panel', show_panel)
        
        if show_panel:
            # Mark all as read when panel is opened
            self.mark_all_as_read()
    
    async def mark_all_as_read(self):
        """Mark all notifications as read"""
        user_id = self.context.user.id
        await Notification.filter(user_id=user_id, read=False).update(read=True)
        
        notifications = self.state.get('notifications')
        for notification in notifications:
            notification['read'] = True
        
        self.state.set_multiple({
            'notifications': notifications,
            'unread_count': 0
        })
    
    def render(self):
        notifications = self.state.get('notifications')
        unread_count = self.state.get('unread_count')
        show_panel = self.state.get('show_panel')
        
        # Notification badge
        badge = f'<span class="badge">{unread_count}</span>' if unread_count > 0 else ''
        
        # Notification list
        notification_items = ''.join([
            f'''
            <div class="notification-item {'unread' if not n['read'] else ''}"
                 onclick="this.component.mark_as_read({n['id']})">
                <div class="notification-icon">{n['icon']}</div>
                <div class="notification-content">
                    <h4>{n['title']}</h4>
                    <p>{n['message']}</p>
                    <small>{n['created_at']}</small>
                </div>
            </div>
            '''
            for n in notifications
        ])
        
        panel_class = 'notification-panel active' if show_panel else 'notification-panel'
        
        return f'''
        <div class="notification-system">
            <button class="notification-button" onclick="this.component.toggle_panel()">
                🔔 {badge}
            </button>
            
            <div class="{panel_class}">
                <div class="panel-header">
                    <h3>Notifications</h3>
                    {f'<button onclick="this.component.mark_all_as_read()">Mark all as read</button>' if unread_count > 0 else ''}
                </div>
                <div class="notification-list">
                    {notification_items or '<p class="empty">No notifications</p>'}
                </div>
            </div>
        </div>
        '''

# Usage: Send notifications from anywhere in your app
async def send_notification(user_id, title, message, icon="📢"):
    notification = await Notification.create(
        user_id=user_id,
        title=title,
        message=message,
        icon=icon
    )
    
    await notification_manager.send(f"user_{user_id}", notification.to_dict())
```

## ⚡ Performance Optimization

### Connection Pooling

```python
from pyframe.realtime import ConnectionPool

# Configure connection pooling
connection_pool = ConnectionPool(
    max_connections=1000,
    cleanup_interval=60,  # seconds
    connection_timeout=300  # 5 minutes
)

# Use with WebSocket manager
ws_manager = WebSocketManager(connection_pool=connection_pool)
```

### Message Queuing

```python
from pyframe.realtime import MessageQueue

# Set up message queue for handling high-volume events
message_queue = MessageQueue(
    backend='redis',  # or 'memory', 'database'
    max_queue_size=10000,
    batch_size=50
)

@message_queue.handler('user_notifications')
async def process_notifications(messages):
    """Process notification messages in batches"""
    for message in messages:
        await send_notification(
            message['user_id'],
            message['title'],
            message['content']
        )

# Queue notifications instead of sending immediately
await message_queue.enqueue('user_notifications', {
    'user_id': 123,
    'title': 'New Message',
    'content': 'You have a new message from Alice'
})
```

## 🔒 Security Considerations

### WebSocket Authentication

```python
async def authenticate_websocket(websocket):
    """Authenticate WebSocket connections"""
    try:
        # Get token from query parameters or headers
        token = websocket.query_params.get('token')
        if not token:
            return None
        
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Verify user exists and is active
        user = await User.get(id=user_id, is_active=True)
        return user
    
    except Exception:
        return None

@app.websocket('/ws/secure')
async def secure_websocket(websocket):
    user = await authenticate_websocket(websocket)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    # Continue with authenticated connection
    await handle_authenticated_websocket(websocket, user)
```

### Rate Limiting

```python
from pyframe.realtime import RateLimiter

rate_limiter = RateLimiter(
    max_requests=100,  # per window
    window_size=60     # seconds
)

@app.websocket('/ws/chat')
async def rate_limited_chat(websocket):
    user = await authenticate_websocket(websocket)
    
    try:
        while True:
            message = await websocket.receive_json()
            
            # Check rate limit
            if not await rate_limiter.allow(f"user_{user.id}"):
                await websocket.send_json({
                    'error': 'Rate limit exceeded',
                    'retry_after': 60
                })
                continue
            
            # Process message
            await process_chat_message(user, message)
    
    except Exception as e:
        print(f"Chat error: {e}")
    finally:
        await ws_manager.disconnect(websocket)
```

## 📚 Best Practices

### 1. Connection Management
```python
# Good: Properly handle connection lifecycle
class WebSocketHandler:
    def __init__(self):
        self.connections = set()
    
    async def connect(self, websocket):
        self.connections.add(websocket)
        await self.send_welcome(websocket)
    
    async def disconnect(self, websocket):
        self.connections.discard(websocket)
        await self.cleanup_user_data(websocket)
    
    async def broadcast(self, message):
        # Remove dead connections
        dead_connections = set()
        for websocket in self.connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)
        
        self.connections -= dead_connections
```

### 2. Error Handling
```python
@app.websocket('/ws/chat')
async def robust_chat(websocket):
    try:
        await ws_manager.connect(websocket)
        
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30 second timeout
                )
                await process_message(message)
            
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.ping()
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    'error': 'Invalid JSON format'
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)
```

### 3. Scalability
```python
# Use Redis for scaling across multiple servers
from pyframe.realtime import RedisBackend

redis_backend = RedisBackend(
    host='localhost',
    port=6379,
    db=0
)

ws_manager = WebSocketManager(backend=redis_backend)

# Messages will be synchronized across all server instances
await ws_manager.broadcast({
    'type': 'announcement',
    'message': 'System maintenance in 5 minutes'
})
```

Real-time features are what make modern web applications feel alive and engaging. PyFrame makes it easy to add these capabilities to your applications! 🚀
