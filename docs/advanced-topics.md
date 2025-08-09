# Advanced Topics

This guide covers advanced PyFrame concepts for building sophisticated, high-performance applications. Master these topics to unlock PyFrame's full potential.

## 🏗️ Custom Component Architecture

### Higher-Order Components (HOCs)

```python
from pyframe import Component, StatefulComponent

def with_loading(WrappedComponent):
    """HOC that adds loading state management"""
    
    class WithLoading(StatefulComponent):
        def __init__(self, **props):
            super().__init__(**props)
            self.state = State({
                'loading': False,
                'error': None
            })
            self.wrapped_component = WrappedComponent(**props)
        
        async def set_loading(self, loading):
            self.state.update('loading', loading)
        
        async def set_error(self, error):
            self.state.update('error', str(error) if error else None)
        
        def render(self):
            loading = self.state.get('loading')
            error = self.state.get('error')
            
            if loading:
                return '<div class="loading-spinner">Loading...</div>'
            
            if error:
                return f'<div class="error-message">Error: {error}</div>'
            
            return self.wrapped_component.render()
    
    return WithLoading

# Usage
@with_loading
class UserProfile(Component):
    def render(self):
        user = self.props.get('user')
        return f'''
        <div class="user-profile">
            <h2>{user['name']}</h2>
            <p>{user['email']}</p>
        </div>
        '''

# The wrapped component automatically gets loading states
profile = UserProfile(user=user_data)
```

### Component Composition Patterns

```python
class Layout(Component):
    """Flexible layout component with slots"""
    
    def render(self):
        header = self.props.get('header', '')
        sidebar = self.props.get('sidebar', '')
        main = self.props.get('main', '')
        footer = self.props.get('footer', '')
        
        return f'''
        <div class="layout">
            <header class="layout-header">{header}</header>
            <div class="layout-body">
                <aside class="layout-sidebar">{sidebar}</aside>
                <main class="layout-main">{main}</main>
            </div>
            <footer class="layout-footer">{footer}</footer>
        </div>
        '''

class PageTemplate(Component):
    """Page template using composition"""
    
    def render(self):
        title = self.props.get('title', 'Page')
        content = self.props.get('content', '')
        
        header = f'<h1>{title}</h1>'
        sidebar = self.render_sidebar()
        footer = self.render_footer()
        
        return Layout(
            header=header,
            sidebar=sidebar,
            main=content,
            footer=footer
        ).render()
    
    def render_sidebar(self):
        return '''
        <nav>
            <a href="/">Home</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
        '''
    
    def render_footer(self):
        return '<p>&copy; 2024 My App. All rights reserved.</p>'
```

### Render Props Pattern

```python
class DataProvider(StatefulComponent):
    """Component that provides data via render props"""
    
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'data': None,
            'loading': True,
            'error': None
        })
    
    async def component_did_mount(self):
        await self.fetch_data()
    
    async def fetch_data(self):
        try:
            self.state.update('loading', True)
            url = self.props.get('url')
            data = await self.http_get(url)
            self.state.set_multiple({
                'data': data,
                'loading': False,
                'error': None
            })
        except Exception as e:
            self.state.set_multiple({
                'loading': False,
                'error': str(e)
            })
    
    def render(self):
        render_fn = self.props.get('render')
        if not render_fn:
            raise ValueError("DataProvider requires a 'render' prop")
        
        return render_fn({
            'data': self.state.get('data'),
            'loading': self.state.get('loading'),
            'error': self.state.get('error'),
            'refetch': self.fetch_data
        })

# Usage
def render_user_list(props):
    if props['loading']:
        return '<div>Loading users...</div>'
    
    if props['error']:
        return f'<div>Error: {props["error"]}</div>'
    
    users = props['data'] or []
    user_items = ''.join([
        f'<li>{user["name"]} - {user["email"]}</li>'
        for user in users
    ])
    
    return f'''
    <div>
        <button onclick="props.refetch()">Refresh</button>
        <ul>{user_items}</ul>
    </div>
    '''

# Use the data provider
data_provider = DataProvider(
    url='/api/users',
    render=render_user_list
)
```

## 🔧 Advanced State Management

### Global State Store

```python
from pyframe.state import GlobalStore
import asyncio

class AppStore(GlobalStore):
    """Global application state store"""
    
    def __init__(self):
        super().__init__()
        self.state = {
            'user': None,
            'theme': 'light',
            'notifications': [],
            'loading': False
        }
        self.middleware = []
    
    def add_middleware(self, middleware):
        """Add middleware for state changes"""
        self.middleware.append(middleware)
    
    async def dispatch(self, action):
        """Dispatch action through middleware chain"""
        for middleware in self.middleware:
            action = await middleware(action, self.state)
            if not action:  # Middleware can cancel action
                return
        
        await self.reduce(action)
    
    async def reduce(self, action):
        """Reduce action to state changes"""
        action_type = action.get('type')
        payload = action.get('payload', {})
        
        if action_type == 'SET_USER':
            self.state['user'] = payload
            self.notify_subscribers('user')
        
        elif action_type == 'SET_THEME':
            self.state['theme'] = payload
            self.notify_subscribers('theme')
        
        elif action_type == 'ADD_NOTIFICATION':
            self.state['notifications'].append(payload)
            self.notify_subscribers('notifications')
        
        elif action_type == 'REMOVE_NOTIFICATION':
            self.state['notifications'] = [
                n for n in self.state['notifications'] 
                if n['id'] != payload['id']
            ]
            self.notify_subscribers('notifications')
        
        elif action_type == 'SET_LOADING':
            self.state['loading'] = payload
            self.notify_subscribers('loading')

# Create global store instance
app_store = AppStore()

# Middleware examples
async def logging_middleware(action, state):
    """Log all actions"""
    print(f"Action: {action['type']}, Payload: {action.get('payload')}")
    return action

async def auth_middleware(action, state):
    """Handle authentication-related side effects"""
    if action['type'] == 'SET_USER':
        user = action['payload']
        if user:
            # User logged in
            await load_user_preferences(user['id'])
        else:
            # User logged out
            await clear_user_data()
    return action

app_store.add_middleware(logging_middleware)
app_store.add_middleware(auth_middleware)

# Connect components to store
class ConnectedComponent(StatefulComponent):
    """Base class for store-connected components"""
    
    def __init__(self, **props):
        super().__init__(**props)
        self.store_subscriptions = []
    
    def connect_to_store(self, keys, callback=None):
        """Connect to specific store keys"""
        if isinstance(keys, str):
            keys = [keys]
        
        for key in keys:
            subscription = app_store.subscribe(key, callback or self.on_store_change)
            self.store_subscriptions.append(subscription)
    
    def on_store_change(self, key, value):
        """Handle store changes"""
        self.state.update(f'store_{key}', value)
    
    def component_will_unmount(self):
        """Clean up store subscriptions"""
        for subscription in self.store_subscriptions:
            subscription.unsubscribe()
```

### State Persistence

```python
from pyframe.state import PersistentState
import json

class PersistentUserPreferences(PersistentState):
    """Persistent user preferences"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.storage_key = f"user_preferences_{user_id}"
        
        super().__init__(
            storage_backend='localStorage',
            key=self.storage_key,
            default_state={
                'theme': 'light',
                'language': 'en',
                'notifications_enabled': True,
                'sidebar_collapsed': False
            }
        )
    
    async def save_to_server(self):
        """Sync preferences to server"""
        try:
            await self.http_post('/api/preferences', {
                'user_id': self.user_id,
                'preferences': self.get_all()
            })
        except Exception as e:
            print(f"Failed to sync preferences: {e}")
    
    async def load_from_server(self):
        """Load preferences from server"""
        try:
            response = await self.http_get(f'/api/preferences/{self.user_id}')
            server_prefs = response.get('preferences', {})
            
            # Merge server preferences with local
            merged_prefs = {**self.get_all(), **server_prefs}
            self.set_multiple(merged_prefs)
        except Exception as e:
            print(f"Failed to load server preferences: {e}")

# Usage in components
class UserSettings(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.user_id = props['user_id']
        self.preferences = PersistentUserPreferences(self.user_id)
        
        self.state = State({
            'preferences': self.preferences.get_all(),
            'saving': False
        })
    
    async def component_did_mount(self):
        # Load from server and merge
        await self.preferences.load_from_server()
        self.state.update('preferences', self.preferences.get_all())
    
    async def update_preference(self, key, value):
        """Update a preference"""
        self.preferences.set(key, value)
        
        prefs = self.state.get('preferences')
        prefs[key] = value
        self.state.update('preferences', prefs)
        
        # Auto-save to server
        self.state.update('saving', True)
        await self.preferences.save_to_server()
        self.state.update('saving', False)
```

## 🚀 Performance Optimization

### Virtual Scrolling

```python
class VirtualList(StatefulComponent):
    """Virtual scrolling list for large datasets"""
    
    def __init__(self, **props):
        super().__init__(**props)
        
        self.items = props.get('items', [])
        self.item_height = props.get('item_height', 50)
        self.container_height = props.get('container_height', 400)
        self.render_item = props.get('render_item')
        
        self.state = State({
            'scroll_top': 0,
            'visible_start': 0,
            'visible_end': 0
        })
        
        self.update_visible_range()
    
    def update_visible_range(self):
        """Calculate which items should be rendered"""
        scroll_top = self.state.get('scroll_top')
        
        # Calculate visible range
        visible_start = max(0, int(scroll_top / self.item_height) - 5)
        visible_count = int(self.container_height / self.item_height) + 10
        visible_end = min(len(self.items), visible_start + visible_count)
        
        self.state.set_multiple({
            'visible_start': visible_start,
            'visible_end': visible_end
        })
    
    def handle_scroll(self, scroll_top):
        """Handle scroll events"""
        self.state.update('scroll_top', scroll_top)
        self.update_visible_range()
    
    def render(self):
        visible_start = self.state.get('visible_start')
        visible_end = self.state.get('visible_end')
        
        # Calculate spacer heights
        top_spacer_height = visible_start * self.item_height
        bottom_spacer_height = (len(self.items) - visible_end) * self.item_height
        
        # Render visible items
        visible_items = ''.join([
            f'<div class="virtual-item" style="height: {self.item_height}px;">' +
            self.render_item(self.items[i], i) +
            '</div>'
            for i in range(visible_start, visible_end)
        ])
        
        return f'''
        <div class="virtual-list" 
             style="height: {self.container_height}px; overflow-y: auto;"
             onscroll="this.component.handle_scroll(this.scrollTop)">
            <div style="height: {top_spacer_height}px;"></div>
            {visible_items}
            <div style="height: {bottom_spacer_height}px;"></div>
        </div>
        '''

# Usage
def render_user_item(user, index):
    return f'''
    <div class="user-item">
        <img src="{user['avatar']}" alt="Avatar">
        <div>
            <h4>{user['name']}</h4>
            <p>{user['email']}</p>
        </div>
    </div>
    '''

virtual_list = VirtualList(
    items=large_user_list,  # 10,000+ items
    item_height=60,
    container_height=400,
    render_item=render_user_item
)
```

### Component Memoization

```python
from pyframe.optimization import memo, use_memo
import hashlib

def memo(deps=None):
    """Memoization decorator for components"""
    def decorator(component_class):
        class MemoizedComponent(component_class):
            _memo_cache = {}
            
            def __init__(self, **props):
                super().__init__(**props)
                self._memo_key = self._generate_memo_key(props, deps)
            
            def _generate_memo_key(self, props, deps):
                """Generate cache key from props and dependencies"""
                if deps:
                    cache_data = {key: props.get(key) for key in deps}
                else:
                    cache_data = props
                
                cache_str = json.dumps(cache_data, sort_keys=True)
                return hashlib.md5(cache_str.encode()).hexdigest()
            
            def render(self):
                """Cached render method"""
                if self._memo_key in self._memo_cache:
                    return self._memo_cache[self._memo_key]
                
                result = super().render()
                self._memo_cache[self._memo_key] = result
                
                # Limit cache size
                if len(self._memo_cache) > 100:
                    # Remove oldest entries
                    keys = list(self._memo_cache.keys())
                    for key in keys[:50]:
                        del self._memo_cache[key]
                
                return result
        
        return MemoizedComponent
    return decorator

# Usage
@memo(deps=['user_id', 'theme'])
class ExpensiveUserCard(Component):
    def render(self):
        # Expensive rendering logic
        user = self.fetch_user_data(self.props['user_id'])
        return self.complex_render(user)

# Custom memoization hook
def use_memo(factory, deps):
    """Memoization hook for computed values"""
    if not hasattr(use_memo, '_cache'):
        use_memo._cache = {}
    
    deps_key = json.dumps(deps, sort_keys=True)
    
    if deps_key not in use_memo._cache:
        use_memo._cache[deps_key] = factory()
    
    return use_memo._cache[deps_key]

# Usage in component
class DataVisualization(StatefulComponent):
    def render(self):
        data = self.props.get('data', [])
        
        # Expensive computation memoized
        processed_data = use_memo(
            lambda: self.process_large_dataset(data),
            deps=[len(data), data[0] if data else None]
        )
        
        return self.render_chart(processed_data)
```

### Code Splitting

```python
from pyframe.code_splitting import lazy_import, Suspense

# Lazy load heavy components
LazyChart = lazy_import('components.chart', 'ChartComponent')
LazyDataTable = lazy_import('components.datatable', 'DataTableComponent')

class Dashboard(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'active_tab': 'overview',
            'chart_data': None,
            'table_data': None
        })
    
    def render(self):
        active_tab = self.state.get('active_tab')
        
        if active_tab == 'overview':
            return self.render_overview()
        
        elif active_tab == 'charts':
            return Suspense(
                fallback='<div>Loading charts...</div>',
                children=LazyChart(data=self.state.get('chart_data'))
            ).render()
        
        elif active_tab == 'data':
            return Suspense(
                fallback='<div>Loading data table...</div>',
                children=LazyDataTable(data=self.state.get('table_data'))
            ).render()
    
    def render_overview(self):
        return '''
        <div class="dashboard-overview">
            <h2>Dashboard Overview</h2>
            <div class="overview-stats">
                <div class="stat-card">
                    <h3>Users</h3>
                    <p>1,234</p>
                </div>
                <div class="stat-card">
                    <h3>Revenue</h3>
                    <p>$12,345</p>
                </div>
            </div>
        </div>
        '''
```

## 🔌 Advanced Plugin Development

### Creating Custom Plugins

```python
from pyframe.plugins import Plugin
from pyframe.hooks import hook

class AnalyticsPlugin(Plugin):
    """Advanced analytics plugin with event tracking"""
    
    def __init__(self, **config):
        super().__init__(**config)
        self.api_key = config.get('api_key')
        self.endpoint = config.get('endpoint', 'https://api.analytics.com')
        self.batch_size = config.get('batch_size', 50)
        self.flush_interval = config.get('flush_interval', 30)
        
        self.event_queue = []
        self.user_sessions = {}
    
    async def initialize(self, app):
        """Initialize plugin with app"""
        self.app = app
        
        # Register hooks
        app.hooks.register('request_started', self.track_page_view)
        app.hooks.register('user_action', self.track_user_action)
        app.hooks.register('error_occurred', self.track_error)
        
        # Start background flush task
        self.flush_task = asyncio.create_task(self.flush_events_periodically())
    
    async def track_page_view(self, context):
        """Track page views"""
        event = {
            'type': 'page_view',
            'path': context.path,
            'user_id': getattr(context.user, 'id', None),
            'session_id': self.get_session_id(context),
            'user_agent': context.headers.get('User-Agent'),
            'ip_address': context.remote_addr,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.queue_event(event)
    
    async def track_user_action(self, action_type, user_id, metadata=None):
        """Track user actions"""
        event = {
            'type': 'user_action',
            'action': action_type,
            'user_id': user_id,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        await self.queue_event(event)
    
    async def track_error(self, error, context):
        """Track errors"""
        event = {
            'type': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'path': context.path,
            'user_id': getattr(context.user, 'id', None),
            'timestamp': datetime.now().isoformat()
        }
        
        await self.queue_event(event)
    
    async def queue_event(self, event):
        """Queue event for batch sending"""
        self.event_queue.append(event)
        
        if len(self.event_queue) >= self.batch_size:
            await self.flush_events()
    
    async def flush_events(self):
        """Send queued events to analytics service"""
        if not self.event_queue:
            return
        
        events = self.event_queue[:]
        self.event_queue.clear()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/events",
                    json={'events': events},
                    headers={'Authorization': f'Bearer {self.api_key}'}
                ) as response:
                    if response.status != 200:
                        # Re-queue events on failure
                        self.event_queue.extend(events)
        
        except Exception as e:
            print(f"Analytics flush error: {e}")
            # Re-queue events on error
            self.event_queue.extend(events)
    
    async def flush_events_periodically(self):
        """Periodically flush events"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush_events()
    
    def get_session_id(self, context):
        """Get or create session ID"""
        session_id = context.session.get('analytics_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            context.session['analytics_session_id'] = session_id
        return session_id

# Plugin usage
analytics = AnalyticsPlugin(
    api_key='your-api-key',
    batch_size=100,
    flush_interval=60
)

app.use_plugin(analytics)

# Track custom events
await analytics.track_user_action('button_click', user.id, {
    'button_id': 'signup',
    'page': '/pricing'
})
```

### Plugin Composition

```python
from pyframe.plugins import PluginManager

class PluginManager:
    """Advanced plugin management with dependencies"""
    
    def __init__(self):
        self.plugins = {}
        self.dependency_graph = {}
        self.hooks = HookRegistry()
    
    def register_plugin(self, name, plugin, dependencies=None):
        """Register plugin with dependencies"""
        self.plugins[name] = plugin
        self.dependency_graph[name] = dependencies or []
    
    async def initialize_plugins(self, app):
        """Initialize plugins in dependency order"""
        ordered_plugins = self.resolve_dependencies()
        
        for plugin_name in ordered_plugins:
            plugin = self.plugins[plugin_name]
            await plugin.initialize(app)
            print(f"Initialized plugin: {plugin_name}")
    
    def resolve_dependencies(self):
        """Topological sort of plugin dependencies"""
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(plugin_name):
            if plugin_name in temp_visited:
                raise ValueError(f"Circular dependency detected: {plugin_name}")
            
            if plugin_name not in visited:
                temp_visited.add(plugin_name)
                
                for dependency in self.dependency_graph.get(plugin_name, []):
                    visit(dependency)
                
                temp_visited.remove(plugin_name)
                visited.add(plugin_name)
                result.append(plugin_name)
        
        for plugin_name in self.plugins:
            if plugin_name not in visited:
                visit(plugin_name)
        
        return result

# Usage
plugin_manager = PluginManager()

# Register plugins with dependencies
plugin_manager.register_plugin('database', DatabasePlugin())
plugin_manager.register_plugin('cache', CachePlugin(), dependencies=['database'])
plugin_manager.register_plugin('auth', AuthPlugin(), dependencies=['database', 'cache'])
plugin_manager.register_plugin('analytics', AnalyticsPlugin(), dependencies=['auth'])

# Initialize in correct order
await plugin_manager.initialize_plugins(app)
```

## 🔍 Advanced Debugging

### Component Development Tools

```python
from pyframe.devtools import DevTools

class DevTools:
    """Development tools for debugging PyFrame apps"""
    
    def __init__(self, app):
        self.app = app
        self.component_tree = {}
        self.performance_logs = []
        self.state_history = []
    
    def track_component_render(self, component, render_time):
        """Track component render performance"""
        component_name = component.__class__.__name__
        
        self.performance_logs.append({
            'component': component_name,
            'render_time': render_time,
            'timestamp': datetime.now(),
            'props': component.props,
            'state': getattr(component, 'state', {})
        })
        
        # Keep only recent logs
        if len(self.performance_logs) > 1000:
            self.performance_logs = self.performance_logs[-500:]
    
    def track_state_change(self, component, key, old_value, new_value):
        """Track state changes"""
        self.state_history.append({
            'component': component.__class__.__name__,
            'key': key,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': datetime.now()
        })
    
    def get_component_tree(self):
        """Get current component tree structure"""
        return self.component_tree
    
    def get_performance_report(self):
        """Generate performance report"""
        if not self.performance_logs:
            return "No performance data available"
        
        # Analyze render times
        component_stats = {}
        for log in self.performance_logs:
            component = log['component']
            if component not in component_stats:
                component_stats[component] = {
                    'count': 0,
                    'total_time': 0,
                    'max_time': 0,
                    'min_time': float('inf')
                }
            
            stats = component_stats[component]
            stats['count'] += 1
            stats['total_time'] += log['render_time']
            stats['max_time'] = max(stats['max_time'], log['render_time'])
            stats['min_time'] = min(stats['min_time'], log['render_time'])
        
        # Calculate averages
        for component, stats in component_stats.items():
            stats['avg_time'] = stats['total_time'] / stats['count']
        
        return component_stats

# Enable devtools in development
if app.config.debug:
    devtools = DevTools(app)
    app.devtools = devtools
```

### Performance Profiling

```python
import cProfile
import pstats
from functools import wraps

def profile_component(func):
    """Decorator to profile component methods"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if app.config.debug:
            profiler = cProfile.Profile()
            profiler.enable()
            
            result = func(*args, **kwargs)
            
            profiler.disable()
            stats = pstats.Stats(profiler)
            
            # Log slow renders
            if stats.total_tt > 0.1:  # 100ms threshold
                print(f"Slow render detected in {func.__name__}: {stats.total_tt:.3f}s")
                stats.sort_stats('cumulative').print_stats(10)
            
            return result
        else:
            return func(*args, **kwargs)
    
    return wrapper

# Usage
class SlowComponent(StatefulComponent):
    @profile_component
    def render(self):
        # Component render logic
        return self.expensive_render_method()
```

This covers the advanced PyFrame topics that will help you build sophisticated, high-performance applications! 🚀
