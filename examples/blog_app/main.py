"""
PyFrame Sample Blog Application

Comprehensive example demonstrating all PyFrame features:
- Reactive components with Python-to-JS compilation
- Automatic context-aware adaptivity  
- Zero-boilerplate data layer with auto-generated APIs
- Real-time updates with WebSockets
- Plugin system (auth, cache, analytics)
- Server-side rendering with hydration
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Optional

# Add parent directory to path for PyFrame imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# PyFrame imports
from pyframe import PyFrameApp, PyFrameConfig
from pyframe.core.component import Component, StatefulComponent, component
from pyframe.data.models import Model, Field, FieldType
from pyframe.data.database import DatabaseManager
from pyframe.plugins.auth_plugin import AuthPlugin, AuthUser, require_auth
from pyframe.plugins.cache_plugin import CachePlugin
from pyframe.plugins.analytics_plugin import AnalyticsPlugin
from pyframe.realtime.live_sync import live_sync_manager
from pyframe.server.context import RequestContext


# Data Models

class BlogPost(Model):
    """Blog post model with automatic API generation"""
    
    title: str = Field(FieldType.STRING, max_length=200)
    slug: str = Field(FieldType.STRING, unique=True, max_length=200)
    content: str = Field(FieldType.TEXT)
    excerpt: str = Field(FieldType.TEXT, required=False)
    author_id: str = Field(FieldType.UUID, foreign_key="AuthUser")
    published: bool = Field(FieldType.BOOLEAN, default=False)
    published_at: Optional[datetime] = Field(FieldType.DATETIME, required=False)
    view_count: int = Field(FieldType.INTEGER, default=0)
    tags: List[str] = Field(FieldType.JSON, default=list)
    
    def save(self):
        """Override save to trigger live updates"""
        result = super().save()
        
        # Notify live sync manager
        asyncio.create_task(
            live_sync_manager.sync_model_change(
                self, 
                'update' if hasattr(self, '_original_id') else 'create'
            )
        )
        
        return result


class Comment(Model):
    """Comment model with real-time updates"""
    
    content: str = Field(FieldType.TEXT)
    author_id: str = Field(FieldType.UUID, foreign_key="AuthUser")
    post_id: str = Field(FieldType.UUID, foreign_key="BlogPost")
    parent_id: Optional[str] = Field(FieldType.UUID, foreign_key="Comment", required=False)
    approved: bool = Field(FieldType.BOOLEAN, default=False)
    
    def save(self):
        result = super().save()
        
        # Trigger real-time comment updates
        asyncio.create_task(
            live_sync_manager.sync_model_change(self, 'create', channel=f"post:{self.post_id}")
        )
        
        return result


# Components

class BlogLayout(StatefulComponent):
    """Main layout component with navigation"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("menu_open", False)
        
    def toggle_menu(self):
        """Toggle mobile menu"""
        current = self.get_state("menu_open", False)
        self.set_state("menu_open", not current)
        
    def render(self) -> str:
        user = self.props.get("user")
        menu_open = self.get_state("menu_open", False)
        menu_class = "menu-open" if menu_open else ""
        
        return f"""
        <div class="blog-layout {menu_class}">
            <header class="header">
                <div class="container">
                    <h1 class="logo">
                        <a href="/">PyFrame Blog</a>
                    </h1>
                    
                    <nav class="nav">
                        <a href="/" class="nav-link">Home</a>
                        <a href="/posts" class="nav-link">Posts</a>
                        {self._render_user_menu(user)}
                    </nav>
                    
                    <button class="menu-toggle" onclick="this.component.toggle_menu()">
                        ☰
                    </button>
                </div>
            </header>
            
            <main class="main">
                <div class="container">
                    {''.join(child.render() if hasattr(child, 'render') else str(child) for child in self.children)}
                </div>
            </main>
            
            <footer class="footer">
                <div class="container">
                    <p>&copy; 2024 PyFrame Blog. Built with PyFrame.</p>
                </div>
            </footer>
        </div>
        """
        
    def _render_user_menu(self, user):
        if user:
            return f"""
            <div class="user-menu">
                <span>Welcome, {user.first_name or user.username}!</span>
                <a href="/profile" class="nav-link">Profile</a>
                <a href="/dashboard" class="nav-link">Dashboard</a>
                <a href="/auth/logout" class="nav-link">Logout</a>
            </div>
            """
        else:
            return """
            <div class="auth-links">
                <a href="/auth/login" class="nav-link">Login</a>
                <a href="/auth/register" class="nav-link">Register</a>
            </div>
            """


class PostCard(Component):
    """Blog post card component"""
    
    def render(self) -> str:
        post = self.props.get("post")
        show_excerpt = self.props.get("show_excerpt", True)
        
        if not post:
            return ""
            
        published_date = post.get("published_at", "").split("T")[0] if post.get("published_at") else ""
        
        excerpt_html = ""
        if show_excerpt and post.get("excerpt"):
            excerpt_html = f'<p class="post-excerpt">{post["excerpt"]}</p>'
            
        tags_html = ""
        if post.get("tags"):
            tag_items = [f'<span class="tag">{tag}</span>' for tag in post["tags"]]
            tags_html = f'<div class="post-tags">{"".join(tag_items)}</div>'
        
        return f"""
        <article class="post-card">
            <h2 class="post-title">
                <a href="/posts/{post.get('slug', '')}">{post.get('title', 'Untitled')}</a>
            </h2>
            
            <div class="post-meta">
                <span class="post-date">{published_date}</span>
                <span class="post-views">{post.get('view_count', 0)} views</span>
            </div>
            
            {excerpt_html}
            {tags_html}
        </article>
        """


class CommentList(StatefulComponent):
    """Real-time comment list component"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        
        post_id = props.get("post_id") if props else None
        comments = self._load_comments(post_id)
        self.set_state("comments", comments)
        self.set_state("loading", False)
        
        # Subscribe to real-time updates for this post
        if post_id:
            live_sync_manager.subscribe_to_model("Comment", f"post:{post_id}")
            
    def _load_comments(self, post_id):
        """Load comments for post"""
        if not post_id:
            return []
            
        try:
            comments = Comment.filter(post_id=post_id, approved=True)
            return [comment.to_dict() for comment in comments]
        except:
            return []
            
    def add_comment(self, content, user_id):
        """Add new comment with real-time update"""
        post_id = self.props.get("post_id")
        if not post_id or not content.strip():
            return
            
        comment = Comment.create(
            content=content,
            author_id=user_id,
            post_id=post_id,
            approved=True  # Auto-approve for demo
        )
        
        # Update local state
        comments = self.get_state("comments", [])
        comments.append(comment.to_dict())
        self.set_state("comments", comments)
        
    def render(self) -> str:
        comments = self.get_state("comments", [])
        loading = self.get_state("loading", False)
        user = self.props.get("user")
        
        if loading:
            return '<div class="comments loading">Loading comments...</div>'
            
        comments_html = ""
        for comment in comments:
            comments_html += f"""
            <div class="comment">
                <div class="comment-meta">
                    <strong>{comment.get('author_name', 'Anonymous')}</strong>
                    <span class="comment-date">{comment.get('created_at', '')}</span>
                </div>
                <div class="comment-content">{comment.get('content', '')}</div>
            </div>
            """
            
        comment_form = ""
        if user:
            comment_form = f"""
            <form class="comment-form" onsubmit="this.component.submit_comment(event)">
                <textarea 
                    name="content" 
                    placeholder="Add a comment..." 
                    rows="3"
                    required
                ></textarea>
                <button type="submit">Post Comment</button>
            </form>
            
            <script>
            // Add comment form handler
            if (typeof window.submitComment === 'undefined') {{
                window.submitComment = function(event, component) {{
                    event.preventDefault();
                    const form = event.target;
                    const content = form.content.value;
                    
                    if (content.trim()) {{
                        component.add_comment(content, '{user.id}');
                        form.reset();
                    }}
                }};
            }}
            </script>
            """
        else:
            comment_form = '<p class="login-prompt"><a href="/auth/login">Login</a> to comment</p>'
            
        return f"""
        <div class="comments-section">
            <h3>Comments ({len(comments)})</h3>
            
            <div class="comments-list">
                {comments_html if comments else '<p class="no-comments">No comments yet.</p>'}
            </div>
            
            {comment_form}
        </div>
        """


class SearchBox(StatefulComponent):
    """Search component with live results"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("query", "")
        self.set_state("results", [])
        self.set_state("searching", False)
        
    def search(self, query):
        """Perform search with debouncing"""
        self.set_state("query", query)
        self.set_state("searching", True)
        
        # Simulate search delay
        import asyncio
        asyncio.create_task(self._perform_search(query))
        
    async def _perform_search(self, query):
        """Perform actual search"""
        await asyncio.sleep(0.3)  # Debounce delay
        
        if query.strip():
            try:
                # Simple search implementation
                posts = BlogPost.filter()
                results = [
                    post.to_dict() for post in posts 
                    if query.lower() in post.title.lower() or 
                       query.lower() in post.content.lower()
                ][:5]  # Limit to 5 results
                
                self.set_state("results", results)
            except:
                self.set_state("results", [])
        else:
            self.set_state("results", [])
            
        self.set_state("searching", False)
        
    def render(self) -> str:
        query = self.get_state("query", "")
        results = self.get_state("results", [])
        searching = self.get_state("searching", False)
        
        results_html = ""
        if searching:
            results_html = '<div class="search-results searching">Searching...</div>'
        elif query and results:
            result_items = ""
            for post in results:
                result_items += f"""
                <a href="/posts/{post['slug']}" class="search-result">
                    <h4>{post['title']}</h4>
                    <p>{post.get('excerpt', '')[:100]}...</p>
                </a>
                """
            results_html = f'<div class="search-results">{result_items}</div>'
        elif query and not results:
            results_html = '<div class="search-results no-results">No results found.</div>'
            
        return f"""
        <div class="search-box">
            <input 
                type="text" 
                placeholder="Search posts..." 
                value="{query}"
                oninput="this.component.search(this.value)"
                class="search-input"
            >
            {results_html}
        </div>
        """


# Page Components

@component
def HomePage(props, children):
    """Home page component"""
    
    # Load recent posts
    try:
        recent_posts = BlogPost.filter(published=True, limit=5, order_by="-published_at")
        posts_data = [post.to_dict() for post in recent_posts]
    except:
        posts_data = []
        
    posts_html = ""
    for post_data in posts_data:
        post_card = PostCard({"post": post_data, "show_excerpt": True})
        posts_html += post_card.render()
        
    search_box = SearchBox()
    
    return f"""
    <div class="home-page">
        <section class="hero">
            <h1>Welcome to PyFrame Blog</h1>
            <p>A modern blog built with the PyFrame full-stack Python framework</p>
            {search_box.render()}
        </section>
        
        <section class="recent-posts">
            <h2>Recent Posts</h2>
            <div class="posts-grid">
                {posts_html if posts_html else '<p>No posts yet.</p>'}
            </div>
        </section>
        
        <section class="features">
            <h2>PyFrame Features</h2>
            <div class="features-grid">
                <div class="feature">
                    <h3>🐍 Python Everywhere</h3>
                    <p>Write both frontend and backend in Python</p>
                </div>
                <div class="feature">
                    <h3>⚡ Reactive Components</h3>
                    <p>Automatic state management and updates</p>
                </div>
                <div class="feature">
                    <h3>🔄 Real-time Updates</h3>
                    <p>Live data synchronization</p>
                </div>
                <div class="feature">
                    <h3>📱 Adaptive Rendering</h3>
                    <p>Automatic optimization for all devices</p>
                </div>
            </div>
        </section>
    </div>
    """


class PostDetailPage(StatefulComponent):
    """Individual post page with comments"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        
        slug = props.get("slug") if props else None
        post = self._load_post(slug)
        
        self.set_state("post", post)
        self.set_state("loading", False)
        
        # Increment view count
        if post:
            try:
                post_obj = BlogPost.get(slug=slug)
                if post_obj:
                    post_obj.view_count += 1
                    post_obj.save()
            except:
                pass
                
    def _load_post(self, slug):
        """Load post by slug"""
        if not slug:
            return None
            
        try:
            post_obj = BlogPost.get(slug=slug, published=True)
            return post_obj.to_dict() if post_obj else None
        except:
            return None
            
    def render(self) -> str:
        post = self.get_state("post")
        loading = self.get_state("loading", False)
        user = self.props.get("user")
        
        if loading:
            return '<div class="post-detail loading">Loading...</div>'
            
        if not post:
            return '''
            <div class="post-detail not-found">
                <h1>Post Not Found</h1>
                <p>The post you're looking for doesn't exist.</p>
                <a href="/">← Back to Home</a>
            </div>
            '''
            
        published_date = post.get("published_at", "").split("T")[0] if post.get("published_at") else ""
        
        tags_html = ""
        if post.get("tags"):
            tag_items = [f'<span class="tag">{tag}</span>' for tag in post["tags"]]
            tags_html = f'<div class="post-tags">{"".join(tag_items)}</div>'
            
        # Comments component
        comments = CommentList({"post_id": post.get("id"), "user": user})
        
        return f"""
        <article class="post-detail">
            <header class="post-header">
                <h1 class="post-title">{post.get('title', 'Untitled')}</h1>
                
                <div class="post-meta">
                    <span class="post-date">{published_date}</span>
                    <span class="post-views">{post.get('view_count', 0)} views</span>
                </div>
                
                {tags_html}
            </header>
            
            <div class="post-content">
                {post.get('content', '')}
            </div>
            
            {comments.render()}
        </article>
        """


# Application Setup

def create_blog_app():
    """Create and configure the blog application"""
    
    # Configuration
    config = PyFrameConfig(
        debug=True,
        hot_reload=True,
        auto_reload=True,
        host="localhost",
        port=3000,
        ssr_enabled=True,
        hydration_strategy="partial",
        database_url="sqlite:///blog.db"
    )
    
    # Create app
    app = PyFrameApp(config)
    
    # Initialize database
    DatabaseManager.initialize(config.database_url)
    DatabaseManager.create_all_tables()
    
    # Register plugins
    auth_plugin = AuthPlugin({
        "jwt_secret": "your-secret-key-change-in-production",
        "password_min_length": 6
    })
    app.register_plugin(auth_plugin)
    
    cache_plugin = CachePlugin({
        "default_ttl": 3600
    })
    app.register_plugin(cache_plugin)
    
    analytics_plugin = AnalyticsPlugin({
        "enabled": True,
        "privacy_mode": True
    })
    app.register_plugin(analytics_plugin)
    
    # Routes
    @app.component_route("/")
    class HomeRoute(BlogLayout):
        def __init__(self, props=None, children=None):
            home_page = HomePage()
            super().__init__(props, [home_page])
            
    @app.component_route("/posts/<slug>")
    class PostRoute(BlogLayout):
        def __init__(self, props=None, children=None):
            post_page = PostDetailPage(props)
            super().__init__(props, [post_page])
            
    # API Routes (auto-generated by data layer)
    from pyframe.data.api_generator import RESTAPIGenerator
    api_generator = RESTAPIGenerator(app.router)
    api_generator.generate_all_apis()
    
    # Static CSS
    @app.route("/static/styles.css")
    async def serve_css(context):
        css = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #fff;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo a {
            color: white;
            text-decoration: none;
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .nav {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background 0.2s;
        }
        
        .nav-link:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .menu-toggle {
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .main {
            min-height: calc(100vh - 200px);
            padding: 2rem 0;
        }
        
        .hero {
            text-align: center;
            padding: 3rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-bottom: 3rem;
            border-radius: 8px;
        }
        
        .hero h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .search-box {
            position: relative;
            max-width: 400px;
            margin: 2rem auto 0;
        }
        
        .search-input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
        }
        
        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-height: 300px;
            overflow-y: auto;
            z-index: 10;
        }
        
        .search-result {
            display: block;
            padding: 1rem;
            text-decoration: none;
            color: #333;
            border-bottom: 1px solid #eee;
        }
        
        .search-result:hover {
            background: #f8f9fa;
        }
        
        .posts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .post-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .post-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .post-title a {
            color: #2c3e50;
            text-decoration: none;
            font-size: 1.25rem;
            font-weight: 600;
        }
        
        .post-meta {
            color: #666;
            font-size: 0.9rem;
            margin: 0.5rem 0;
        }
        
        .post-excerpt {
            margin: 1rem 0;
            color: #555;
        }
        
        .post-tags {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        
        .tag {
            background: #e9ecef;
            color: #495057;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .feature {
            text-align: center;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .feature h3 {
            margin-bottom: 1rem;
            color: #2c3e50;
        }
        
        .comments-section {
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 2px solid #eee;
        }
        
        .comment {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .comment-meta {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        
        .comment-form {
            margin-top: 2rem;
        }
        
        .comment-form textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            resize: vertical;
            font-family: inherit;
        }
        
        .comment-form button {
            background: #007bff;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 0.5rem;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 2rem 0;
            margin-top: 3rem;
        }
        
        @media (max-width: 768px) {
            .nav { display: none; }
            .menu-toggle { display: block; }
            .menu-open .nav { 
                display: flex;
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: #2c3e50;
                flex-direction: column;
                padding: 1rem;
            }
            .hero h1 { font-size: 2rem; }
            .posts-grid { grid-template-columns: 1fr; }
        }
        """
        
        return {
            "status": 200,
            "headers": {"Content-Type": "text/css"},
            "body": css
        }
    
    # Create some sample data
    create_sample_data()
    
    return app


def create_sample_data():
    """Create sample blog posts and users"""
    
    try:
        # Create admin user
        admin = AuthUser.get(username="admin")
        if not admin:
            admin = AuthUser(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                is_staff=True,
                is_superuser=True
            )
            admin.set_password("admin123")
            admin.save()
            
        # Create sample posts
        if not BlogPost.filter():
            posts_data = [
                {
                    "title": "Welcome to PyFrame",
                    "slug": "welcome-to-pyframe",
                    "content": """
                    <p>PyFrame is a revolutionary full-stack Python web framework that allows you to build modern web applications using Python for both frontend and backend development.</p>
                    
                    <h3>Key Features</h3>
                    <ul>
                        <li>Write frontend components in Python</li>
                        <li>Automatic compilation to efficient JavaScript</li>
                        <li>Real-time data synchronization</li>
                        <li>Context-aware adaptive rendering</li>
                        <li>Zero-boilerplate data layer</li>
                    </ul>
                    
                    <p>This blog is built entirely with PyFrame to demonstrate all of its capabilities!</p>
                    """,
                    "excerpt": "PyFrame is a revolutionary full-stack Python web framework for modern web applications.",
                    "tags": ["pyframe", "python", "web-development"],
                    "published": True,
                    "published_at": datetime.now()
                },
                {
                    "title": "Reactive Components in Python",
                    "slug": "reactive-components-python",
                    "content": """
                    <p>One of PyFrame's most powerful features is the ability to write reactive UI components entirely in Python.</p>
                    
                    <h3>Component Example</h3>
                    <pre><code>
class Counter(StatefulComponent):
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("count", 0)
        
    def increment(self):
        count = self.get_state("count", 0)
        self.set_state("count", count + 1)
        
    def render(self):
        count = self.get_state("count", 0)
        return f'''
        &lt;div&gt;
            &lt;p&gt;Count: {count}&lt;/p&gt;
            &lt;button onclick="this.component.increment()"&gt;
                Increment
            &lt;/button&gt;
        &lt;/div&gt;
        '''
                    </code></pre>
                    
                    <p>The component automatically compiles to JavaScript and maintains reactive state!</p>
                    """,
                    "excerpt": "Learn how to build reactive UI components using Python syntax.",
                    "tags": ["components", "reactive", "tutorial"],
                    "published": True,
                    "published_at": datetime.now()
                }
            ]
            
            for post_data in posts_data:
                post = BlogPost(
                    title=post_data["title"],
                    slug=post_data["slug"],
                    content=post_data["content"],
                    excerpt=post_data["excerpt"],
                    author_id=str(admin.id),
                    published=post_data["published"],
                    published_at=post_data["published_at"],
                    tags=post_data["tags"]
                )
                post.save()
                
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")


if __name__ == "__main__":
    # Create and run the blog application
    app = create_blog_app()
    
    print("🚀 Starting PyFrame Blog Application...")
    print("📖 Features demonstrated:")
    print("   • Reactive Python components")
    print("   • Automatic Python-to-JS compilation") 
    print("   • Real-time comments with WebSockets")
    print("   • Context-aware adaptive rendering")
    print("   • Auto-generated REST APIs")
    print("   • Authentication with JWT")
    print("   • Caching and analytics plugins")
    print("   • Hot reload development server")
    print("")
    
    app.run()
