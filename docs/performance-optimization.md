# Performance Optimization

Optimize your PyFrame applications for maximum speed, efficiency, and scalability. This guide covers all aspects of performance optimization.

## 📊 Performance Fundamentals

### Understanding Performance Metrics

```python
import time
import psutil
import asyncio
from functools import wraps

class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'requests_processed': 0,
            'total_response_time': 0,
            'avg_response_time': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
    
    def track_request(self, response_time):
        """Track request response time"""
        self.metrics['requests_processed'] += 1
        self.metrics['total_response_time'] += response_time
        self.metrics['avg_response_time'] = (
            self.metrics['total_response_time'] / 
            self.metrics['requests_processed']
        )
    
    def track_resources(self):
        """Track system resource usage"""
        process = psutil.Process()
        self.metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
        self.metrics['cpu_usage'] = process.cpu_percent()
    
    def get_metrics(self):
        """Get current performance metrics"""
        self.track_resources()
        return self.metrics.copy()

# Global performance monitor
perf_monitor = PerformanceMonitor()

def performance_middleware(app):
    """Middleware to track request performance"""
    
    async def middleware(context, call_next):
        start_time = time.time()
        
        response = await call_next(context)
        
        response_time = time.time() - start_time
        perf_monitor.track_request(response_time)
        
        # Add performance headers
        response.setdefault('headers', {})
        response['headers']['X-Response-Time'] = f"{response_time:.3f}s"
        
        return response
    
    return middleware
```

## 🚀 Component Optimization

### Component Memoization

```python
from functools import lru_cache
import json
import hashlib

class MemoizedComponent:
    """Base class for memoized components"""
    
    _render_cache = {}
    _cache_hits = 0
    _cache_misses = 0
    
    def __init__(self, **props):
        self.props = props
        self._memo_key = self._generate_memo_key()
    
    def _generate_memo_key(self):
        """Generate cache key from props"""
        props_str = json.dumps(self.props, sort_keys=True, default=str)
        return hashlib.md5(props_str.encode()).hexdigest()
    
    def render(self):
        """Memoized render method"""
        if self._memo_key in self._render_cache:
            self._cache_hits += 1
            return self._render_cache[self._memo_key]
        
        self._cache_misses += 1
        result = self._render_impl()
        
        # Cache management - limit cache size
        if len(self._render_cache) > 1000:
            # Remove oldest 20% of entries
            keys_to_remove = list(self._render_cache.keys())[:200]
            for key in keys_to_remove:
                del self._render_cache[key]
        
        self._render_cache[self._memo_key] = result
        return result
    
    def _render_impl(self):
        """Implement this method with actual render logic"""
        raise NotImplementedError
    
    @classmethod
    def get_cache_stats(cls):
        """Get cache performance statistics"""
        total = cls._cache_hits + cls._cache_misses
        hit_rate = cls._cache_hits / total if total > 0 else 0
        return {
            'hits': cls._cache_hits,
            'misses': cls._cache_misses,
            'hit_rate': hit_rate,
            'cache_size': len(cls._render_cache)
        }

# Usage
class ProductCard(MemoizedComponent):
    """Memoized product card component"""
    
    def _render_impl(self):
        product = self.props['product']
        show_description = self.props.get('show_description', True)
        
        description = (
            f'<p class="description">{product["description"]}</p>'
            if show_description else ''
        )
        
        return f'''
        <div class="product-card">
            <img src="{product['image']}" alt="{product['name']}">
            <h3>{product['name']}</h3>
            <span class="price">${product['price']}</span>
            {description}
        </div>
        '''

# Efficient list rendering
class ProductList(Component):
    def render(self):
        products = self.props['products']
        show_descriptions = self.props.get('show_descriptions', True)
        
        # Each product card is memoized
        product_cards = [
            ProductCard(
                product=product,
                show_description=show_descriptions
            ).render()
            for product in products
        ]
        
        return f'''
        <div class="product-list">
            {''.join(product_cards)}
        </div>
        '''
```

### Virtual Scrolling for Large Lists

```python
class VirtualScrollList(StatefulComponent):
    """Virtual scrolling for large datasets"""
    
    def __init__(self, **props):
        super().__init__(**props)
        
        self.items = props['items']
        self.item_height = props.get('item_height', 50)
        self.container_height = props.get('container_height', 400)
        self.overscan = props.get('overscan', 5)  # Extra items to render
        self.render_item = props['render_item']
        
        self.state = State({
            'scroll_top': 0,
            'visible_start': 0,
            'visible_count': 0
        })
        
        self._update_visible_range()
    
    def _update_visible_range(self):
        """Calculate which items should be visible"""
        scroll_top = self.state.get('scroll_top')
        
        # Calculate visible range
        start_index = max(0, int(scroll_top / self.item_height) - self.overscan)
        visible_count = int(self.container_height / self.item_height) + (2 * self.overscan)
        
        self.state.set_multiple({
            'visible_start': start_index,
            'visible_count': min(visible_count, len(self.items) - start_index)
        })
    
    def handle_scroll(self, scroll_top):
        """Handle scroll events efficiently"""
        # Throttle scroll updates
        if abs(scroll_top - self.state.get('scroll_top')) > 10:
            self.state.update('scroll_top', scroll_top)
            self._update_visible_range()
    
    def render(self):
        visible_start = self.state.get('visible_start')
        visible_count = self.state.get('visible_count')
        visible_end = visible_start + visible_count
        
        # Calculate spacer heights
        top_spacer = visible_start * self.item_height
        bottom_spacer = (len(self.items) - visible_end) * self.item_height
        
        # Render only visible items
        visible_items = []
        for i in range(visible_start, min(visible_end, len(self.items))):
            item_html = self.render_item(self.items[i], i)
            visible_items.append(
                f'<div class="virtual-item" style="height: {self.item_height}px;" data-index="{i}">'
                f'{item_html}'
                f'</div>'
            )
        
        return f'''
        <div class="virtual-scroll-container" 
             style="height: {self.container_height}px; overflow-y: auto;"
             onscroll="this.component.handle_scroll(this.scrollTop)">
            
            <div class="virtual-spacer-top" style="height: {top_spacer}px;"></div>
            
            <div class="virtual-items">
                {''.join(visible_items)}
            </div>
            
            <div class="virtual-spacer-bottom" style="height: {bottom_spacer}px;"></div>
        </div>
        '''

# Usage with 100,000 items
large_dataset = [{'id': i, 'name': f'Item {i}'} for i in range(100000)]

def render_item(item, index):
    return f'<span>{item["name"]}</span>'

virtual_list = VirtualScrollList(
    items=large_dataset,
    item_height=40,
    container_height=600,
    render_item=render_item
)
```

### Lazy Component Loading

```python
import asyncio
from functools import wraps

class LazyComponent:
    """Lazy-loaded component with loading states"""
    
    def __init__(self, loader, fallback="Loading..."):
        self.loader = loader  # Function that returns component
        self.fallback = fallback
        self._component = None
        self._loading = False
        self._error = None
    
    async def load(self):
        """Load the component asynchronously"""
        if self._component or self._loading:
            return
        
        try:
            self._loading = True
            self._component = await self.loader()
        except Exception as e:
            self._error = str(e)
        finally:
            self._loading = False
    
    def render(self, **props):
        """Render component or fallback"""
        if self._error:
            return f'<div class="error">Error loading component: {self._error}</div>'
        
        if self._component:
            return self._component(**props).render()
        
        if not self._loading:
            # Start loading
            asyncio.create_task(self.load())
        
        return f'<div class="loading">{self.fallback}</div>'

# Component factory functions
async def load_chart_component():
    """Simulate loading heavy charting component"""
    await asyncio.sleep(0.1)  # Simulate network delay
    
    class ChartComponent(Component):
        def render(self):
            data = self.props.get('data', [])
            return f'<div class="chart">Chart with {len(data)} data points</div>'
    
    return ChartComponent

async def load_data_table():
    """Simulate loading data table component"""
    await asyncio.sleep(0.05)
    
    class DataTable(Component):
        def render(self):
            rows = self.props.get('rows', [])
            return f'<table class="data-table">Table with {len(rows)} rows</table>'
    
    return DataTable

# Create lazy components
LazyChart = LazyComponent(load_chart_component, "Loading chart...")
LazyTable = LazyComponent(load_data_table, "Loading table...")

class Dashboard(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({'active_tab': 'overview'})
    
    def render(self):
        active_tab = self.state.get('active_tab')
        
        return f'''
        <div class="dashboard">
            <nav class="tab-nav">
                <button onclick="this.component.set_tab('overview')"
                        class="{'active' if active_tab == 'overview' else ''}">
                    Overview
                </button>
                <button onclick="this.component.set_tab('charts')"
                        class="{'active' if active_tab == 'charts' else ''}">
                    Charts
                </button>
                <button onclick="this.component.set_tab('data')"
                        class="{'active' if active_tab == 'data' else ''}">
                    Data
                </button>
            </nav>
            
            <div class="tab-content">
                {self.render_tab_content(active_tab)}
            </div>
        </div>
        '''
    
    def render_tab_content(self, tab):
        if tab == 'overview':
            return '<div class="overview">Dashboard Overview</div>'
        elif tab == 'charts':
            # Lazy load chart component
            return LazyChart.render(data=self.get_chart_data())
        elif tab == 'data':
            # Lazy load table component
            return LazyTable.render(rows=self.get_table_data())
    
    def set_tab(self, tab):
        self.state.update('active_tab', tab)
```

## 🗃️ Database Optimization

### Query Optimization

```python
from pyframe import Model, Field, FieldType

class OptimizedUserQuery:
    """Optimized user data queries"""
    
    @staticmethod
    async def get_user_with_posts(user_id, limit=10):
        """Get user with their recent posts in one query"""
        # Use select_related to avoid N+1 queries
        user = await User.select_related('profile').get(id=user_id)
        
        # Get posts with eager loading
        posts = await (Post
                      .select_related('author')
                      .filter(author_id=user_id)
                      .order_by('-created_at')
                      .limit(limit))
        
        user._posts = posts  # Attach posts to user object
        return user
    
    @staticmethod
    async def get_users_with_post_counts():
        """Get users with their post counts using aggregation"""
        from pyframe.models import Count
        
        return await (User
                     .annotate(post_count=Count('posts'))
                     .order_by('-post_count'))
    
    @staticmethod
    async def search_users_optimized(query, page=1, page_size=20):
        """Optimized user search with pagination"""
        offset = (page - 1) * page_size
        
        # Use database full-text search if available
        users = await (User
                      .filter(name__icontains=query)
                      .select_related('profile')
                      .offset(offset)
                      .limit(page_size))
        
        # Get total count for pagination
        total_count = await User.filter(name__icontains=query).count()
        
        return {
            'users': users,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }

# Bulk operations for better performance
class BulkOperations:
    """Efficient bulk database operations"""
    
    @staticmethod
    async def bulk_create_users(user_data_list):
        """Create multiple users efficiently"""
        users = [User(**data) for data in user_data_list]
        return await User.bulk_create(users)
    
    @staticmethod
    async def bulk_update_user_status(user_ids, status):
        """Update multiple users at once"""
        return await User.filter(id__in=user_ids).update(status=status)
    
    @staticmethod
    async def bulk_delete_old_posts(days_old=30):
        """Delete old posts in batch"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        return await Post.filter(created_at__lt=cutoff_date).delete()
```

### Connection Pooling

```python
import asyncpg
from pyframe.database import DatabasePool

class OptimizedDatabasePool:
    """Optimized database connection pool"""
    
    def __init__(self, database_url, **pool_config):
        self.database_url = database_url
        self.pool_config = {
            'min_size': 5,
            'max_size': 20,
            'max_queries': 50000,
            'max_inactive_connection_lifetime': 300,
            'command_timeout': 60,
            **pool_config
        }
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            **self.pool_config
        )
    
    async def execute_query(self, query, *args):
        """Execute query with connection from pool"""
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def execute_transaction(self, queries):
        """Execute multiple queries in a transaction"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                results = []
                for query, args in queries:
                    result = await connection.fetch(query, *args)
                    results.append(result)
                return results
    
    async def get_pool_stats(self):
        """Get connection pool statistics"""
        return {
            'size': self.pool.get_size(),
            'min_size': self.pool.get_min_size(),
            'max_size': self.pool.get_max_size(),
            'idle_size': self.pool.get_idle_size()
        }
    
    async def close(self):
        """Close all connections"""
        if self.pool:
            await self.pool.close()
```

## 🌐 HTTP and Caching Optimization

### Response Caching

```python
import hashlib
import pickle
from datetime import datetime, timedelta

class ResponseCache:
    """HTTP response caching system"""
    
    def __init__(self, backend='memory', default_ttl=300):
        self.backend = backend
        self.default_ttl = default_ttl
        self._memory_cache = {}
        
        if backend == 'redis':
            import redis
            self.redis = redis.Redis()
    
    def generate_cache_key(self, context):
        """Generate cache key from request context"""
        key_parts = [
            context.method,
            context.path,
            sorted(context.query_params.items()) if context.query_params else '',
            context.headers.get('Accept', ''),
            getattr(context.user, 'id', 'anonymous') if hasattr(context, 'user') else 'anonymous'
        ]
        
        key_string = '|'.join(str(part) for part in key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, key):
        """Get cached response"""
        if self.backend == 'memory':
            cached = self._memory_cache.get(key)
            if cached and cached['expires'] > datetime.now():
                return cached['data']
            elif cached:
                # Expired, remove from cache
                del self._memory_cache[key]
        
        elif self.backend == 'redis':
            data = self.redis.get(key)
            if data:
                return pickle.loads(data)
        
        return None
    
    async def set(self, key, data, ttl=None):
        """Cache response data"""
        ttl = ttl or self.default_ttl
        
        if self.backend == 'memory':
            self._memory_cache[key] = {
                'data': data,
                'expires': datetime.now() + timedelta(seconds=ttl)
            }
            
            # Clean up expired entries periodically
            if len(self._memory_cache) > 1000:
                self._cleanup_expired()
        
        elif self.backend == 'redis':
            self.redis.setex(key, ttl, pickle.dumps(data))
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self._memory_cache.items()
            if value['expires'] <= now
        ]
        for key in expired_keys:
            del self._memory_cache[key]

# Caching middleware
def create_cache_middleware(cache_config=None):
    """Create caching middleware"""
    cache = ResponseCache(**(cache_config or {}))
    
    async def cache_middleware(context, call_next):
        # Only cache GET requests
        if context.method != 'GET':
            return await call_next(context)
        
        # Check for cache control headers
        if context.headers.get('Cache-Control') == 'no-cache':
            return await call_next(context)
        
        # Generate cache key
        cache_key = cache.generate_cache_key(context)
        
        # Try to get cached response
        cached_response = await cache.get(cache_key)
        if cached_response:
            # Add cache hit header
            cached_response.setdefault('headers', {})
            cached_response['headers']['X-Cache'] = 'HIT'
            return cached_response
        
        # Process request
        response = await call_next(context)
        
        # Cache successful responses
        if response.get('status', 200) == 200:
            # Determine TTL from response headers
            ttl = 300  # Default 5 minutes
            if 'Cache-Control' in response.get('headers', {}):
                # Parse max-age from Cache-Control
                cache_control = response['headers']['Cache-Control']
                if 'max-age=' in cache_control:
                    ttl = int(cache_control.split('max-age=')[1].split(',')[0])
            
            await cache.set(cache_key, response, ttl)
            
            # Add cache miss header
            response.setdefault('headers', {})
            response['headers']['X-Cache'] = 'MISS'
        
        return response
    
    return cache_middleware
```

### Static Asset Optimization

```python
import gzip
import hashlib
from pathlib import Path

class StaticAssetOptimizer:
    """Optimize static assets for better performance"""
    
    def __init__(self, static_dir, optimize_config=None):
        self.static_dir = Path(static_dir)
        self.config = {
            'enable_gzip': True,
            'enable_etags': True,
            'cache_max_age': 31536000,  # 1 year
            'gzip_threshold': 1024,  # Gzip files larger than 1KB
            **optimize_config or {}
        }
        self._file_cache = {}
    
    async def serve_static_file(self, file_path, context):
        """Serve optimized static file"""
        full_path = self.static_dir / file_path
        
        if not full_path.exists():
            return {'status': 404, 'body': 'File not found'}
        
        # Get file info
        file_stat = full_path.stat()
        file_size = file_stat.st_size
        file_mtime = file_stat.st_mtime
        
        # Generate ETag
        if self.config['enable_etags']:
            etag = hashlib.md5(f"{file_path}{file_mtime}{file_size}".encode()).hexdigest()
            
            # Check if client has cached version
            if context.headers.get('If-None-Match') == etag:
                return {'status': 304}  # Not Modified
        
        # Read file content
        cache_key = f"{file_path}:{file_mtime}"
        if cache_key in self._file_cache:
            content = self._file_cache[cache_key]
        else:
            with open(full_path, 'rb') as f:
                content = f.read()
            self._file_cache[cache_key] = content
        
        # Determine content type
        content_type = self._get_content_type(full_path.suffix)
        
        # Prepare headers
        headers = {
            'Content-Type': content_type,
            'Cache-Control': f'public, max-age={self.config["cache_max_age"]}',
        }
        
        if self.config['enable_etags']:
            headers['ETag'] = etag
        
        # Apply gzip compression if beneficial
        if (self.config['enable_gzip'] and 
            file_size > self.config['gzip_threshold'] and
            'gzip' in context.headers.get('Accept-Encoding', '') and
            content_type.startswith(('text/', 'application/javascript', 'application/css'))):
            
            content = gzip.compress(content)
            headers['Content-Encoding'] = 'gzip'
        
        headers['Content-Length'] = str(len(content))
        
        return {
            'status': 200,
            'headers': headers,
            'body': content
        }
    
    def _get_content_type(self, file_extension):
        """Get content type from file extension"""
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
```

## ⚡ Application-Level Optimizations

### Background Task Processing

```python
import asyncio
from queue import Queue
import concurrent.futures

class BackgroundTaskProcessor:
    """Process background tasks efficiently"""
    
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.workers = []
        self.running = False
    
    async def start(self):
        """Start background task workers"""
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Stop background task workers"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Close thread pool
        self.thread_pool.shutdown(wait=True)
    
    async def _worker(self, name):
        """Background task worker"""
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Process task
                await self._process_task(task)
                
                # Mark task as done
                self.task_queue.task_done()
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {name} error: {e}")
    
    async def _process_task(self, task):
        """Process individual task"""
        task_type = task['type']
        task_data = task['data']
        
        if task_type == 'send_email':
            await self._send_email(task_data)
        elif task_type == 'process_image':
            await self._process_image(task_data)
        elif task_type == 'generate_report':
            await self._generate_report(task_data)
        elif task_type == 'cpu_intensive':
            # Run CPU-intensive task in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                self._cpu_intensive_task,
                task_data
            )
    
    async def queue_task(self, task_type, data):
        """Queue a background task"""
        task = {'type': task_type, 'data': data}
        await self.task_queue.put(task)
    
    async def _send_email(self, email_data):
        """Send email asynchronously"""
        # Simulate email sending
        await asyncio.sleep(0.1)
        print(f"Email sent to {email_data['to']}")
    
    async def _process_image(self, image_data):
        """Process image asynchronously"""
        # Simulate image processing
        await asyncio.sleep(0.2)
        print(f"Processed image {image_data['filename']}")
    
    async def _generate_report(self, report_data):
        """Generate report asynchronously"""
        # Simulate report generation
        await asyncio.sleep(0.5)
        print(f"Generated report {report_data['type']}")
    
    def _cpu_intensive_task(self, data):
        """CPU-intensive task that runs in thread pool"""
        # Simulate CPU-intensive work
        import time
        time.sleep(0.1)
        return f"Processed {data}"

# Global task processor
task_processor = BackgroundTaskProcessor()

# Usage in routes
@app.route('/send-notification')
async def send_notification(context):
    user_id = context.json['user_id']
    message = context.json['message']
    
    # Queue background task instead of blocking
    await task_processor.queue_task('send_email', {
        'to': f'user_{user_id}@example.com',
        'subject': 'Notification',
        'body': message
    })
    
    return {'status': 200, 'message': 'Notification queued'}
```

### Memory Management

```python
import gc
import weakref
from typing import Dict, Any
import psutil

class MemoryManager:
    """Monitor and manage application memory usage"""
    
    def __init__(self, max_memory_mb=1024):
        self.max_memory_mb = max_memory_mb
        self.tracked_objects = weakref.WeakSet()
        self.cache_size_limit = 1000
    
    def track_object(self, obj):
        """Track object for memory monitoring"""
        self.tracked_objects.add(obj)
    
    def get_memory_usage(self):
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'tracked_objects': len(self.tracked_objects)
        }
    
    def should_cleanup(self):
        """Check if memory cleanup is needed"""
        memory_usage = self.get_memory_usage()
        return memory_usage['rss_mb'] > self.max_memory_mb
    
    def cleanup_memory(self):
        """Perform memory cleanup"""
        # Force garbage collection
        collected = gc.collect()
        
        # Clear various caches
        self._clear_component_cache()
        self._clear_query_cache()
        
        memory_after = self.get_memory_usage()
        
        return {
            'objects_collected': collected,
            'memory_after_mb': memory_after['rss_mb']
        }
    
    def _clear_component_cache(self):
        """Clear component render cache"""
        from your_components import MemoizedComponent
        if hasattr(MemoizedComponent, '_render_cache'):
            cache_size = len(MemoizedComponent._render_cache)
            if cache_size > self.cache_size_limit:
                # Keep only most recent 50% of cache
                items = list(MemoizedComponent._render_cache.items())
                items_to_keep = items[cache_size // 2:]
                MemoizedComponent._render_cache = dict(items_to_keep)
    
    def _clear_query_cache(self):
        """Clear database query cache"""
        # Implementation depends on your ORM
        pass

# Memory monitoring middleware
memory_manager = MemoryManager(max_memory_mb=2048)

async def memory_monitoring_middleware(context, call_next):
    """Monitor memory usage per request"""
    
    response = await call_next(context)
    
    # Check memory usage after request
    if memory_manager.should_cleanup():
        cleanup_result = memory_manager.cleanup_memory()
        print(f"Memory cleanup: {cleanup_result}")
    
    return response
```

## 📈 Performance Monitoring

### Application Performance Monitoring

```python
import time
import statistics
from collections import defaultdict, deque

class APMCollector:
    """Application Performance Monitoring collector"""
    
    def __init__(self, max_samples=1000):
        self.max_samples = max_samples
        self.metrics = defaultdict(lambda: deque(maxlen=max_samples))
        self.counters = defaultdict(int)
        self.start_time = time.time()
    
    def record_metric(self, name, value, tags=None):
        """Record a performance metric"""
        metric_key = f"{name}:{':'.join(tags or [])}"
        self.metrics[metric_key].append({
            'value': value,
            'timestamp': time.time()
        })
    
    def increment_counter(self, name, tags=None):
        """Increment a counter metric"""
        counter_key = f"{name}:{':'.join(tags or [])}"
        self.counters[counter_key] += 1
    
    def get_metric_stats(self, name, tags=None):
        """Get statistics for a metric"""
        metric_key = f"{name}:{':'.join(tags or [])}"
        values = [m['value'] for m in self.metrics[metric_key]]
        
        if not values:
            return None
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def _percentile(self, values, percentile):
        """Calculate percentile"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_dashboard_data(self):
        """Get data for performance dashboard"""
        uptime = time.time() - self.start_time
        
        dashboard = {
            'uptime_seconds': uptime,
            'counters': dict(self.counters),
            'metrics': {}
        }
        
        for metric_name in self.metrics:
            dashboard['metrics'][metric_name] = self.get_metric_stats(metric_name)
        
        return dashboard

# Global APM instance
apm = APMCollector()

# Performance decorators
def monitor_performance(metric_name=None, tags=None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                apm.increment_counter('function_calls', tags=['status:success'] + (tags or []))
                return result
            except Exception as e:
                apm.increment_counter('function_calls', tags=['status:error'] + (tags or []))
                raise
            finally:
                execution_time = time.time() - start_time
                apm.record_metric('execution_time', execution_time, tags=[f'function:{name}'] + (tags or []))
        
        return wrapper
    return decorator

# Usage
@monitor_performance('database.user_query', ['operation:select'])
async def get_user_by_id(user_id):
    # Database query implementation
    return await User.get(id=user_id)

# Performance dashboard route
@app.route('/admin/performance')
async def performance_dashboard(context):
    dashboard_data = apm.get_dashboard_data()
    
    return {
        'status': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(dashboard_data)
    }
```

Follow these optimization techniques to build blazing-fast PyFrame applications that can handle high traffic and large datasets efficiently! ⚡
