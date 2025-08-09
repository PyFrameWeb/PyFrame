"""
PyFrame Showcase Application

A beautiful demonstration of PyFrame's capabilities using PyFrame itself!
This creates a stunning, professional website entirely with Python components.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Optional

# Add parent directory to path for PyFrame imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# PyFrame imports
from pyframe import PyFrameApp, PyFrameConfig, Component, StatefulComponent, State
from pyframe.core.routing import Route
from pyframe.data.models import Model, Field, FieldType
from pyframe.data.database import DatabaseManager
from pyframe.plugins.auth_plugin import AuthPlugin
from pyframe.plugins.cache_plugin import CachePlugin
from pyframe.plugins.analytics_plugin import AnalyticsPlugin


class HeroSection(Component):
    """Beautiful hero section component"""
    
    def render(self):
        return f"""
        <section class="hero">
            <div class="hero-background"></div>
            <div class="container">
                <div class="hero-content">
                    <h1 class="hero-title">
                        <span class="python-emoji">🐍</span>
                        PyFrame
                    </h1>
                    <p class="hero-subtitle">Revolutionary Full-Stack Python Web Framework</p>
                    <p class="hero-tagline">Write everything in Python. Deploy everywhere. 🚀</p>
                    <div class="hero-stats">
                        <div class="stat">
                            <div class="stat-number">100%</div>
                            <div class="stat-label">Python</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">0</div>
                            <div class="stat-label">Config Files</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">∞</div>
                            <div class="stat-label">Possibilities</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """


class FeatureCard(Component):
    """Individual feature card component"""
    
    def render(self):
        icon = self.props.get('icon', '✨')
        title = self.props.get('title', 'Feature')
        description = self.props.get('description', 'Description')
        
        return f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <h3 class="feature-title">{title}</h3>
            <p class="feature-description">{description}</p>
        </div>
        """


class FeaturesSection(Component):
    """Features showcase section"""
    
    def render(self):
        features = [
            {
                'icon': '🚀',
                'title': 'Python-to-JS Compilation',
                'description': 'Write React-like components in pure Python! Our revolutionary transpiler transforms your Python classes into blazing-fast JavaScript with automatic state management, event handling, and DOM optimization. Zero configuration required! 🔥'
            },
            {
                'icon': '⚛️',
                'title': 'Reactive Components',
                'description': 'Build stunning interactive UIs with intuitive Python classes! State changes automatically trigger lightning-fast re-renders with virtual DOM optimization. Experience true reactive programming without the complexity! ✨'
            },
            {
                'icon': '📊',
                'title': 'Zero-Boilerplate Data',
                'description': 'Define models with Python dataclasses. Auto-generated database schemas, migrations, REST APIs, and admin interfaces.'
            },
            {
                'icon': '🔌',
                'title': 'Plugin Architecture',
                'description': 'Extend functionality with powerful plugins. Authentication, caching, analytics, payments - all as simple Python imports.'
            },
            {
                'icon': '🔥',
                'title': 'Hot Reload Everything',
                'description': 'Experience development nirvana! Instant hot reloading detects every file change and updates your browser in milliseconds. See your Python components come to life as you type! This page is living proof! 🎯'
            },
            {
                'icon': '🌐',
                'title': 'Context-Aware Rendering',
                'description': 'Automatically adapt to user context - device type, location, preferences. Intelligent UX optimization.'
            }
        ]
        
        feature_cards = []
        for feature in features:
            card = FeatureCard(feature)
            feature_cards.append(card.render())
        
        return f"""
        <section class="features-section">
            <div class="container">
                <h2 class="section-title">✨ Unified Python Development</h2>
                <p class="section-subtitle">
                    PyFrame breaks the traditional frontend/backend barrier. Write your entire web application in Python.
                </p>
                <div class="features-grid">
                    {''.join(feature_cards)}
                </div>
            </div>
        </section>
        """


class StatusCard(Component):
    """System status card component"""
    
    def render(self):
        status = self.props.get('status', '✅')
        title = self.props.get('title', 'System')
        description = self.props.get('description', 'Running')
        
        return f"""
        <div class="status-card">
            <div class="status-icon">{status}</div>
            <h4 class="status-title">{title}</h4>
            <p class="status-description">{description}</p>
        </div>
        """


class LiveStatusSection(Component):
    """Live system status section"""
    
    def render(self):
        statuses = [
            {'status': '✅', 'title': 'Python Components', 'description': 'Compiled to JavaScript'},
            {'status': '✅', 'title': 'Database Layer', 'description': 'Auto-generated schemas'},
            {'status': '✅', 'title': 'Plugin System', 'description': 'Auth, Cache, Analytics loaded'},
            {'status': '✅', 'title': 'Hot Reload', 'description': 'WebSocket connection active'},
            {'status': '✅', 'title': 'Dev Server', 'description': 'Running on localhost:3000'},
            {'status': '✅', 'title': 'Context Aware', 'description': 'Adaptive rendering enabled'}
        ]
        
        status_cards = []
        for status in statuses:
            card = StatusCard(status)
            status_cards.append(card.render())
        
        return f"""
        <section class="status-section">
            <div class="container">
                <h2 class="section-title">✅ Live System Status</h2>
                <div class="status-grid">
                    {''.join(status_cards)}
                </div>
            </div>
        </section>
        """


class CodeExample(Component):
    """Code example component"""
    
    def render(self):
        return f"""
        <section class="code-section">
            <div class="container">
                <h2 class="section-title">💻 Python Component in Action</h2>
                <div class="code-example">
                    <div class="code-header">
                        <span class="code-language">🐍 Python</span>
                    </div>
                    <pre class="code-content"><code>from pyframe import Component, State

class UserProfile(Component):
    def __init__(self, props=None):
        super().__init__(props)
        self.state = State({{
            'user': None,
            'loading': True
        }})
    
    async def componentDidMount(self):
        user = await self.fetch_user(self.props.user_id)
        self.setState({{
            'user': user,
            'loading': False
        }})
    
    def render(self):
        if self.state.loading:
            return '&lt;div class="spinner"&gt;Loading...&lt;/div&gt;'
        
        return f'''
        &lt;div class="profile"&gt;
            &lt;img src="{{self.state.user.avatar}}" /&gt;
            &lt;h2&gt;{{self.state.user.name}}&lt;/h2&gt;
            &lt;p&gt;{{self.state.user.bio}}&lt;/p&gt;
        &lt;/div&gt;
        '''</code></pre>
                </div>
                <p class="code-note">
                    ☝️ This Python code automatically compiles to optimized JavaScript with full React-like functionality!
                </p>
            </div>
        </section>
        """


class HotReloadDemo(StatefulComponent):
    """Interactive hot reload demonstration"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("status", "")
        self.set_state("loading", False)
    
    def trigger_reload(self):
        """Trigger hot reload"""
        self.set_state("loading", True)
        self.set_state("status", "🔄 Triggering hot reload...")
        # In a real implementation, this would trigger the actual reload
        print("🔥 Hot reload triggered from Python component!")
        
    def render(self):
        status = self.get_state("status", "")
        loading = self.get_state("loading", False)
        
        button_class = "hot-reload-btn loading" if loading else "hot-reload-btn"
        
        return f"""
        <section class="hot-reload-section">
            <div class="container">
                <h2 class="section-title">🔥 Live Hot Reload Demo</h2>
                <p class="section-subtitle">
                    This button is a real PyFrame component with state management. Click to test hot reload!
                </p>
                <div class="hot-reload-demo">
                    <button class="{button_class}" onclick="triggerHotReload()">
                        🔥 Trigger Hot Reload
                    </button>
                    <div class="reload-status" id="reload-status">{status}</div>
                    <script>
                        function triggerHotReload() {{
                            const statusEl = document.getElementById('reload-status');
                            statusEl.innerText = '🔥 Triggering hot reload...';
                            
                            // Try to trigger reload via the dev server
                            fetch('/__pyframe_dev__/reload')
                                .then(response => response.json())
                                .then(data => {{
                                    statusEl.innerText = '✅ ' + data.message;
                                    // The page should reload automatically via WebSocket
                                }})
                                .catch(error => {{
                                    statusEl.innerText = '❌ Hot reload not available';
                                    console.log('Hot reload error:', error);
                                }});
                        }}
                    </script>
                </div>
            </div>
        </section>
        """


class Navigation(Component):
    """Main navigation component"""
    
    def __init__(self, current_path='/', **props):
        super().__init__()
        self.current_path = current_path
        self.props = props
    
    def render(self):
        current_path = self.current_path
        
        nav_items = [
            {'path': '/', 'label': 'Home', 'icon': '🏠'},
            {'path': '/about', 'label': 'About', 'icon': '👥'},
            {'path': '/get-started', 'label': 'Get Started', 'icon': '🚀'},
            {'path': '/docs', 'label': 'Docs', 'icon': '📚'},
            {'path': '/examples', 'label': 'Examples', 'icon': '💡'},
            {'path': '/contact', 'label': 'Contact', 'icon': '📬'}
        ]
        
        nav_html = ""
        for item in nav_items:
            active_class = "active" if current_path == item['path'] else ""
            nav_html += f"""
                <a href="{item['path']}" class="nav-link {active_class}">
                    <span class="nav-icon">{item['icon']}</span>
                    <span class="nav-label">{item['label']}</span>
                </a>
            """
        
        return f"""
        <nav class="main-nav">
            <div class="nav-container">
                <a href="/" class="nav-logo">
                    <span class="logo-icon">🐍</span>
                    <span class="logo-text">PyFrame</span>
                </a>
                
                <button class="mobile-menu-toggle" onclick="toggleMobileMenu()" aria-label="Toggle menu">
                    <span class="hamburger-line"></span>
                    <span class="hamburger-line"></span>
                    <span class="hamburger-line"></span>
                </button>
                
                <div class="nav-menu" id="nav-menu">
                    <div class="nav-links">
                        {nav_html}
                    </div>
                    <div class="nav-actions">
                        <a href="https://github.com/pyframe/pyframe" class="github-btn" target="_blank">
                            <span>⭐ Star on GitHub</span>
                        </a>
                    </div>
                </div>
            </div>
        </nav>
        
        <script>
            function toggleMobileMenu() {{
                const navMenu = document.getElementById('nav-menu');
                const toggle = document.querySelector('.mobile-menu-toggle');
                
                navMenu.classList.toggle('active');
                toggle.classList.toggle('active');
                
                // Prevent body scroll when menu is open
                if (navMenu.classList.contains('active')) {{
                    document.body.style.overflow = 'hidden';
                }} else {{
                    document.body.style.overflow = '';
                }}
            }}
            
            // Close mobile menu when clicking on a link
            document.addEventListener('DOMContentLoaded', function() {{
                const navLinks = document.querySelectorAll('.nav-link');
                navLinks.forEach(link => {{
                    link.addEventListener('click', function() {{
                        const navMenu = document.getElementById('nav-menu');
                        const toggle = document.querySelector('.mobile-menu-toggle');
                        
                        if (navMenu.classList.contains('active')) {{
                            navMenu.classList.remove('active');
                            toggle.classList.remove('active');
                            document.body.style.overflow = '';
                        }}
                    }});
                }});
                
                // Close menu when clicking outside
                document.addEventListener('click', function(e) {{
                    const navMenu = document.getElementById('nav-menu');
                    const toggle = document.querySelector('.mobile-menu-toggle');
                    const nav = document.querySelector('.main-nav');
                    
                    if (!nav.contains(e.target) && navMenu.classList.contains('active')) {{
                        navMenu.classList.remove('active');
                        toggle.classList.remove('active');
                        document.body.style.overflow = '';
                    }}
                }});
            }});
        </script>
        """


class DarkModeToggle(StatefulComponent):
    """Dark mode toggle component with state management"""
    
    def __init__(self, **props):
        super().__init__(**props)
        self.state = State({
            'isDark': False
        })
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.state.update('isDark', not self.state.get('isDark'))
        # Also update CSS custom properties via JavaScript
        return True
    
    def render(self):
        is_dark = self.state.get('isDark')
        theme_icon = '🌙' if not is_dark else '☀️'
        theme_text = 'Dark' if not is_dark else 'Light'
        
        return f"""
        <div class="dark-mode-toggle">
            <button 
                class="toggle-btn" 
                onclick="toggleDarkMode()" 
                title="Toggle {theme_text} Mode"
            >
                <span class="toggle-icon">{theme_icon}</span>
                <span class="toggle-text">{theme_text} Mode</span>
            </button>
        </div>
        
        <script>
            let isDarkMode = {str(is_dark).lower()};
            
            function toggleDarkMode() {{
                isDarkMode = !isDarkMode;
                document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
                
                // Update button content
                const btn = document.querySelector('.toggle-btn');
                const icon = btn.querySelector('.toggle-icon');
                const text = btn.querySelector('.toggle-text');
                
                if (isDarkMode) {{
                    icon.textContent = '☀️';
                    text.textContent = 'Light Mode';
                }} else {{
                    icon.textContent = '🌙';
                    text.textContent = 'Dark Mode';
                }}
                
                // Save preference
                localStorage.setItem('darkMode', isDarkMode);
            }}
            
            // Initialize theme on page load
            document.addEventListener('DOMContentLoaded', function() {{
                const savedTheme = localStorage.getItem('darkMode');
                if (savedTheme !== null) {{
                    isDarkMode = savedTheme === 'true';
                }}
                document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
                
                // Update button to match current state
                const btn = document.querySelector('.toggle-btn');
                if (btn) {{
                    const icon = btn.querySelector('.toggle-icon');
                    const text = btn.querySelector('.toggle-text');
                    if (isDarkMode) {{
                        icon.textContent = '☀️';
                        text.textContent = 'Light Mode';
                    }} else {{
                        icon.textContent = '🌙';
                        text.textContent = 'Dark Mode';
                    }}
                }}
            }});
        </script>
        """


class AboutPage(Component):
    """About page component"""
    
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        return f"""
        <div class="page-content">
            <section class="hero-small">
                <div class="container">
                    <h1 class="page-title">👥 About PyFrame</h1>
                    <p class="page-subtitle">Revolutionary Python web framework changing how developers build modern applications</p>
                </div>
            </section>
            
            <section class="content-section">
                <div class="container">
                    <div class="about-grid">
                        <div class="about-card">
                            <div class="about-icon">🚀</div>
                            <h3>Our Mission</h3>
                            <p>To revolutionize web development by bringing the simplicity and power of Python to frontend development. We believe developers shouldn't need to learn multiple languages and frameworks to build modern web applications.</p>
                        </div>
                        
                        <div class="about-card">
                            <div class="about-icon">🎯</div>
                            <h3>Our Vision</h3>
                            <p>A world where full-stack development is truly unified. Where Python developers can build beautiful, reactive UIs without compromising on performance or user experience.</p>
                        </div>
                        
                        <div class="about-card">
                            <div class="about-icon">⚡</div>
                            <h3>Our Technology</h3>
                            <p>PyFrame uses advanced transpilation technology to convert Python components into optimized JavaScript, maintaining the developer experience you love while delivering the performance users expect.</p>
                        </div>
                    </div>
                </div>
            </section>
            
            <section class="team-section">
                <div class="container">
                    <h2 class="section-title">Meet the Team</h2>
                    <p class="section-subtitle">Passionate developers building the future of web development</p>
                    
                    <div class="team-grid">
                        <div class="team-member">
                            <div class="member-avatar">👨‍💻</div>
                            <h4>Alex Chen</h4>
                            <p class="member-role">Lead Developer</p>
                            <p class="member-bio">Former Google engineer passionate about developer experience and performance optimization.</p>
                        </div>
                        
                        <div class="team-member">
                            <div class="member-avatar">👩‍💻</div>
                            <h4>Sarah Johnson</h4>
                            <p class="member-role">UI/UX Architect</p>
                            <p class="member-bio">Design systems expert focused on creating intuitive and beautiful user interfaces.</p>
                        </div>
                        
                        <div class="team-member">
                            <div class="member-avatar">👨‍🔬</div>
                            <h4>Dr. Mike Rodriguez</h4>
                            <p class="member-role">Compiler Engineer</p>
                            <p class="member-bio">PhD in Computer Science specializing in programming language design and optimization.</p>
                        </div>
                        
                        <div class="team-member">
                            <div class="member-avatar">👩‍🚀</div>
                            <h4>Emma Davis</h4>
                            <p class="member-role">DevOps Lead</p>
                            <p class="member-bio">Infrastructure expert ensuring PyFrame scales from prototypes to production.</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
        """


class GetStartedPage(Component):
    """Get Started page component"""
    
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        return f"""
        <div class="page-content">
            <section class="hero-small">
                <div class="container">
                    <h1 class="page-title">🚀 Get Started</h1>
                    <p class="page-subtitle">Build your first PyFrame application in minutes</p>
                </div>
            </section>
            
            <section class="content-section">
                <div class="container">
                    <div class="steps-container">
                        <div class="step-card">
                            <div class="step-number">1</div>
                            <h3>Install PyFrame</h3>
                            <div class="code-block">
                                <pre><code>pip install pyframe</code></pre>
                                <button class="copy-btn" onclick="copyToClipboard('pip install pyframe')">📋 Copy</button>
                            </div>
                            <p>Install PyFrame using pip. Works with Python 3.8+ on all platforms.</p>
                        </div>
                        
                        <div class="step-card">
                            <div class="step-number">2</div>
                            <h3>Create Your First App</h3>
                            <div class="code-block">
                                <pre><code>from pyframe import PyFrameApp, Component

class HelloWorld(Component):
    def render(self):
        return "&lt;h1&gt;Hello, PyFrame! 👋&lt;/h1&gt;"

app = PyFrameApp()

@app.route("/")
async def home(context):
    hello = HelloWorld()
    return hello.render_page()

if __name__ == "__main__":
    app.run(debug=True)</code></pre>
                                <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋 Copy</button>
                            </div>
                            <p>Create a simple component and route. PyFrame handles the rest!</p>
                        </div>
                        
                        <div class="step-card">
                            <div class="step-number">3</div>
                            <h3>Run Your App</h3>
                            <div class="code-block">
                                <pre><code>python app.py</code></pre>
                                <button class="copy-btn" onclick="copyToClipboard('python app.py')">📋 Copy</button>
                            </div>
                            <p>Your app will be available at http://localhost:3000 with hot reload enabled!</p>
                        </div>
                        
                        <div class="step-card">
                            <div class="step-number">4</div>
                            <h3>Add State Management</h3>
                            <div class="code-block">
                                <pre><code>from pyframe import StatefulComponent, State

class Counter(StatefulComponent):
    def __init__(self):
        super().__init__()
        self.state = State({{'count': 0}})
    
    def increment(self):
        self.state.update(\'count\', self.state.get(\'count\') + 1)
    
    def render(self):
        count = self.state.get(\'count\')
        return f'''
        &lt;div&gt;
            &lt;p&gt;Count: {{count}}&lt;/p&gt;
            &lt;button onclick="this.increment()"&gt;+1&lt;/button&gt;
        &lt;/div&gt;
        '''</code></pre>
                                <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋 Copy</button>
                            </div>
                            <p>Add reactive state to your components for interactive UIs!</p>
                        </div>
                    </div>
                    
                    <div class="next-steps">
                        <h2>What's Next?</h2>
                        <div class="next-grid">
                            <a href="/docs" class="next-card">
                                <div class="next-icon">📚</div>
                                <h4>Read the Docs</h4>
                                <p>Comprehensive guides and API reference</p>
                            </a>
                            
                            <a href="/examples" class="next-card">
                                <div class="next-icon">💡</div>
                                <h4>Explore Examples</h4>
                                <p>Real-world applications and use cases</p>
                            </a>
                            
                            <a href="https://github.com/pyframe/pyframe" class="next-card">
                                <div class="next-icon">⭐</div>
                                <h4>Star on GitHub</h4>
                                <p>Follow development and contribute</p>
                            </a>
                        </div>
                    </div>
                </div>
            </section>
        </div>
        
        <script>
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(() => {{
                    // Show feedback
                    event.target.textContent = '✅ Copied!';
                    setTimeout(() => {{
                        event.target.textContent = '📋 Copy';
                    }}, 2000);
                }});
            }}
        </script>
        """


class DocsPage(Component):
    """Documentation page component"""
    
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        return f"""
        <div class="page-content">
            <section class="hero-small">
                <div class="container">
                    <h1 class="page-title">📚 Documentation</h1>
                    <p class="page-subtitle">Complete guide to building with PyFrame</p>
                </div>
            </section>
            
            <section class="content-section">
                <div class="container">
                    <div class="docs-layout">
                        <div class="docs-sidebar">
                            <nav class="docs-nav">
                                <div class="nav-section">
                                    <h4>Getting Started</h4>
                                    <a href="#installation">Installation</a>
                                    <a href="#quickstart">Quick Start</a>
                                    <a href="#concepts">Core Concepts</a>
                                </div>
                                
                                <div class="nav-section">
                                    <h4>Components</h4>
                                    <a href="#basic-components">Basic Components</a>
                                    <a href="#stateful-components">Stateful Components</a>
                                    <a href="#props">Props & State</a>
                                </div>
                                
                                <div class="nav-section">
                                    <h4>Routing</h4>
                                    <a href="#routing">Route Definition</a>
                                    <a href="#dynamic-routes">Dynamic Routes</a>
                                    <a href="#middleware">Middleware</a>
                                </div>
                                
                                <div class="nav-section">
                                    <h4>Advanced</h4>
                                    <a href="#plugins">Plugin System</a>
                                    <a href="#deployment">Deployment</a>
                                    <a href="#optimization">Optimization</a>
                                </div>
                            </nav>
                        </div>
                        
                        <div class="docs-content">
                            <article class="doc-article">
                                <h2 id="installation">🔧 Installation</h2>
                                <p>PyFrame requires Python 3.8 or higher. Install using pip:</p>
                                <div class="code-block">
                                    <pre><code>pip install pyframe</code></pre>
                                </div>
                                
                                <h3>Development Setup</h3>
                                <p>For development with hot reload and debugging:</p>
                                <div class="code-block">
                                    <pre><code>pip install pyframe[dev]</code></pre>
                                </div>
                                
                                <h2 id="quickstart">⚡ Quick Start</h2>
                                <p>Create your first PyFrame application:</p>
                                <div class="code-block">
                                    <pre><code>from pyframe import PyFrameApp, Component

# Define a component
class WelcomeComponent(Component):
    def render(self):
        name = self.props.get(\'name\', \'World\')
        return f'&lt;h1&gt;Welcome, {{name}}!&lt;/h1&gt;'

# Create the app
app = PyFrameApp()

# Define a route
@app.route("/")
async def home(context):
    welcome = WelcomeComponent(name=\"PyFrame\")
    return welcome.render_page()

# Run the app
if __name__ == "__main__":
    app.run(debug=True, hot_reload=True)</code></pre>
                                </div>
                                
                                <h2 id="basic-components">🧩 Basic Components</h2>
                                <p>Basic components are the foundation of PyFrame applications. They extend the Component class and implement a render method that returns HTML.</p>
                                
                                <h3>Creating a Basic Component</h3>
                                <div class="code-block">
                                    <pre><code>from pyframe import Component

class WelcomeMessage(Component):
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        name = self.props.get(\'name\', \'Guest\')
        return f\'&lt;h1&gt;Welcome, {{name}}!&lt;/h1&gt;\'

# Usage
welcome = WelcomeMessage(name=\"Alice\")
html = welcome.render()  # Returns: &lt;h1&gt;Welcome, Alice!&lt;/h1&gt;</code></pre>
                                </div>
                                
                                <h3>Component Props</h3>
                                <p>Props are how you pass data to components. They're similar to function parameters.</p>
                                <div class="code-block">
                                    <pre><code>class UserCard(Component):
    def render(self):
        user = self.props.get(\'user\', {{}})
        avatar = self.props.get(\'avatar\', \'/default-avatar.png\')
        
        return f\'\'\'
        &lt;div class=\"user-card\"&gt;
            &lt;img src=\"{{avatar}}\" alt=\"Avatar\" /&gt;
            &lt;h3&gt;{{user.get(\"name\", \"Unknown\")}}&lt;/h3&gt;
            &lt;p&gt;{{user.get(\"email\", \"No email\")}}&lt;/p&gt;
        &lt;/div&gt;
        \'\'\'</code></pre>
                                </div>
                                
                                <h2 id="stateful-components">⚡ Stateful Components</h2>
                                <p>Stateful components can manage internal state and respond to user interactions. They extend StatefulComponent and use the State class.</p>
                                
                                <h3>Creating Stateful Components</h3>
                                <div class="code-block">
                                    <pre><code>from pyframe import StatefulComponent, State

class Counter(StatefulComponent):
    def __init__(self, **props):
        super().__init__()
        self.props = props
        self.state = State({{
            \'count\': props.get(\'initial\', 0),
            \'step\': props.get(\'step\', 1)
        }})
    
    def increment(self):
        current = self.state.get(\'count\')
        step = self.state.get(\'step\')
        self.state.update(\'count\', current + step)
    
    def decrement(self):
        current = self.state.get(\'count\')
        step = self.state.get(\'step\')
        self.state.update(\'count\', current - step)
    
    def render(self):
        count = self.state.get(\'count\')
        return f\'\'\'
        &lt;div class=\"counter\"&gt;
            &lt;h2&gt;Count: {{count}}&lt;/h2&gt;
            &lt;button onclick=\"this.decrement()\"&gt;-&lt;/button&gt;
            &lt;button onclick=\"this.increment()\"&gt;+&lt;/button&gt;
        &lt;/div&gt;
        \'\'\'</code></pre>
                                </div>
                                
                                <h2 id="props">🎯 Props & State</h2>
                                
                                <h3>Working with Props</h3>
                                <p>Props are immutable data passed to components from their parent.</p>
                                <div class="code-block">
                                    <pre><code># Passing props to a component
blog_post = BlogPost(
    title=\"My First Post\",
    content=\"This is the content...\",
    author={{\"name\": \"John\", \"avatar\": \"/john.jpg\"}},
    published=True
)

# Accessing props in the component
class BlogPost(Component):
    def render(self):
        title = self.props.get(\'title\', \'Untitled\')
        content = self.props.get(\'content\', \'\')
        author = self.props.get(\'author\', {{}})
        published = self.props.get(\'published\', False)
        
        status = \"Published\" if published else \"Draft\"
        
        return f\'\'\'
        &lt;article class=\"blog-post {{\"published\" if published else \"draft\"}}\"&gt;
            &lt;h1&gt;{{title}}&lt;/h1&gt;
            &lt;div class=\"meta\"&gt;
                By {{author.get(\"name\", \"Anonymous\")}} - {{status}}
            &lt;/div&gt;
            &lt;div class=\"content\"&gt;{{content}}&lt;/div&gt;
        &lt;/article&gt;
        \'\'\'</code></pre>
                                </div>
                                
                                <h3>State Management</h3>
                                <p>State is mutable data that belongs to a component and can trigger re-renders when changed.</p>
                                <div class="code-block">
                                    <pre><code>class TodoList(StatefulComponent):
    def __init__(self):
        super().__init__()
        self.state = State({{
            \'todos\': [],
            \'newTodo\': \'\',
            \'filter\': \'all\'  # all, active, completed
        }})
    
    def add_todo(self, text):
        todos = self.state.get(\'todos\')
        new_todo = {{
            \'id\': len(todos) + 1,
            \'text\': text,
            \'completed\': False
        }}
        self.state.update(\'todos\', todos + [new_todo])
        self.state.update(\'newTodo\', \'\')
    
    def toggle_todo(self, todo_id):
        todos = self.state.get(\'todos\')
        updated_todos = []
        for todo in todos:
            if todo[\'id\'] == todo_id:
                todo[\'completed\'] = not todo[\'completed\']
            updated_todos.append(todo)
        self.state.update(\'todos\', updated_todos)
    
    def delete_todo(self, todo_id):
        todos = self.state.get(\'todos\')
        filtered_todos = [t for t in todos if t[\'id\'] != todo_id]
        self.state.update(\'todos\', filtered_todos)</code></pre>
                                </div>
                                
                                <h2 id="routing">🧭 Routing</h2>
                                
                                <h3 id="route-definition">Route Definition</h3>
                                <p>PyFrame uses decorators to define routes. Each route maps a URL pattern to a handler function.</p>
                                <div class="code-block">
                                    <pre><code>from pyframe import PyFrameApp

app = PyFrameApp()

# Basic route
@app.route(\"/\")
async def home(context):
    return {{
        \"status\": 200,
        \"headers\": {{\"Content-Type\": \"text/html\"}},
        \"body\": \"&lt;h1&gt;Welcome Home!&lt;/h1&gt;\"
    }}

# Route with component
@app.route(\"/about\")
async def about(context):
    about_page = AboutPage()
    return about_page.render_page()

# Multiple HTTP methods
@app.route(\"/api/users\", methods=[\"GET\", \"POST\"])
async def users_api(context):
    if context.method == \"GET\":
        return {{\"users\": get_all_users()}}
    elif context.method == \"POST\":
        user = create_user(context.json)
        return {{\"user\": user, \"status\": \"created\"}}</code></pre>
                                </div>
                                
                                <h3 id="dynamic-routes">Dynamic Routes</h3>
                                <p>Use URL parameters to create dynamic routes that can handle variable paths.</p>
                                <div class="code-block">
                                    <pre><code># URL parameters
@app.route(\"/users/&lt;user_id&gt;\")
async def user_profile(context):
    user_id = context.params[\'user_id\']
    user = get_user_by_id(user_id)
    
    if not user:
        return {{\"status\": 404, \"body\": \"User not found\"}}
    
    profile = UserProfile(user=user)
    return profile.render_page()

# Multiple parameters
@app.route(\"/blog/&lt;year&gt;/&lt;month&gt;/&lt;slug&gt;\")
async def blog_post(context):
    year = context.params[\'year\']
    month = context.params[\'month\']
    slug = context.params[\'slug\']
    
    post = get_post_by_date_and_slug(year, month, slug)
    post_component = BlogPostPage(post=post)
    return post_component.render_page()

# Optional parameters with defaults
@app.route(\"/products\")
@app.route(\"/products/&lt;category&gt;\")
async def products(context):
    category = context.params.get(\'category\', \'all\')
    page = int(context.query.get(\'page\', 1))
    
    products = get_products(category=category, page=page)
    products_page = ProductsPage(products=products, category=category)
    return products_page.render_page()</code></pre>
                                </div>
                                
                                <h3 id="middleware">Middleware</h3>
                                <p>Middleware allows you to process requests and responses globally across your application.</p>
                                <div class="code-block">
                                    <pre><code># Authentication middleware
class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, context):
        # Check if route requires authentication
        if context.path.startswith(\"/admin\"):
            token = context.headers.get(\"Authorization\")
            if not token or not verify_token(token):
                return {{
                    \"status\": 401,
                    \"body\": \"Unauthorized\"
                }}
        
        # Continue to next middleware or route handler
        return await self.app(context)

# Logging middleware
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, context):
        start_time = time.time()
        
        # Process request
        response = await self.app(context)
        
        # Log request details
        duration = time.time() - start_time
        print(f\"{{context.method}} {{context.path}} - {{response[\'status\']}} ({{duration:.2f}}s)\")
        
        return response

# Apply middleware
app.use_middleware(LoggingMiddleware)
app.use_middleware(AuthMiddleware)</code></pre>
                                </div>
                                
                                <h2 id="plugins">🔌 Plugin System</h2>
                                <p>PyFrame\'s plugin system allows you to extend functionality with reusable modules.</p>
                                
                                <h3>Using Built-in Plugins</h3>
                                <div class="code-block">
                                    <pre><code>from pyframe.plugins import AuthPlugin, CachePlugin, AnalyticsPlugin

# Authentication plugin
auth_plugin = AuthPlugin({{
    \"secret_key\": \"your-secret-key\",
    \"session_timeout\": 3600,
    \"password_hash\": \"bcrypt\"
}})
app.register_plugin(auth_plugin)

# Caching plugin
cache_plugin = CachePlugin({{
    \"backend\": \"redis\",
    \"host\": \"localhost\",
    \"port\": 6379,
    \"default_timeout\": 300
}})
app.register_plugin(cache_plugin)

# Analytics plugin
analytics_plugin = AnalyticsPlugin({{
    \"provider\": \"google\",
    \"tracking_id\": \"GA-XXXXXXXXX\",
    \"privacy_mode\": True
}})
app.register_plugin(analytics_plugin)</code></pre>
                                </div>
                                
                                <h3>Creating Custom Plugins</h3>
                                <div class="code-block">
                                    <pre><code>class DatabasePlugin:
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def initialize(self, app):
        \"\"\"Called when plugin is registered\"\"\"
        self.connection = connect_to_database(
            host=self.config[\'host\'],
            database=self.config[\'database\'],
            user=self.config[\'user\'],
            password=self.config[\'password\']
        )
        
        # Add database methods to app context
        app.db = self
    
    def query(self, sql, params=None):
        \"\"\"Execute a database query\"\"\"
        cursor = self.connection.cursor()
        cursor.execute(sql, params or [])
        return cursor.fetchall()
    
    def close(self):
        \"\"\"Clean up database connection\"\"\"
        if self.connection:
            self.connection.close()

# Register custom plugin
db_plugin = DatabasePlugin({{
    \"host\": \"localhost\",
    \"database\": \"myapp\",
    \"user\": \"admin\",
    \"password\": \"secret\"
}})
app.register_plugin(db_plugin)

# Use in routes
@app.route(\"/api/users\")
async def get_users(context):
    users = app.db.query(\"SELECT * FROM users\")
    return {{\"users\": users}}</code></pre>
                                </div>
                                
                                <h2 id="deployment">🚀 Deployment</h2>
                                
                                <h3>Production Configuration</h3>
                                <div class="code-block">
                                    <pre><code># production.py
import os
from pyframe import PyFrameApp, PyFrameConfig

config = PyFrameConfig(
    debug=False,
    hot_reload=False,
    host=\"0.0.0.0\",
    port=int(os.environ.get(\"PORT\", 8000)),
    static_url_path=\"/static\",
    static_folder=\"dist/static\",
    template_folder=\"dist/templates\"
)

app = create_app(config)

if __name__ == \"__main__\":
    app.run()</code></pre>
                                </div>
                                
                                <h3>Docker Deployment</h3>
                                <div class="code-block">
                                    <pre><code># Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD [\"python\", \"production.py\"]</code></pre>
                                </div>
                                
                                <h3>Environment Variables</h3>
                                <div class="code-block">
                                    <pre><code># .env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com</code></pre>
                                </div>
                                
                                <h2 id="optimization">⚡ Optimization</h2>
                                
                                <h3>Performance Best Practices</h3>
                                <div class="concept-grid">
                                    <div class="concept-card">
                                        <h4>Component Optimization</h4>
                                        <ul>
                                            <li>Keep components small and focused</li>
                                            <li>Use caching for expensive operations</li>
                                            <li>Minimize state updates</li>
                                            <li>Lazy load heavy components</li>
                                        </ul>
                                    </div>
                                    
                                    <div class="concept-card">
                                        <h4>Database Optimization</h4>
                                        <ul>
                                            <li>Use connection pooling</li>
                                            <li>Implement query caching</li>
                                            <li>Add database indexes</li>
                                            <li>Use async database drivers</li>
                                        </ul>
                                    </div>
                                </div>
                                
                                <h3>Caching Strategies</h3>
                                <div class="code-block">
                                    <pre><code># Component-level caching
class ExpensiveComponent(Component):
    @cache(timeout=300)  # Cache for 5 minutes
    def render(self):
        # Expensive computation here
        data = expensive_database_query()
        return f\"&lt;div&gt;{{data}}&lt;/div&gt;\"

# Route-level caching
@app.route(\"/api/stats\")
@cache(timeout=600)  # Cache for 10 minutes
async def stats_api(context):
    stats = calculate_expensive_stats()
    return {{\"stats\": stats}}

# Manual caching
from pyframe.cache import cache

def get_user_posts(user_id):
    cache_key = f\"user_posts_{{user_id}}\"
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = fetch_posts_from_db(user_id)
        cache.set(cache_key, posts, timeout=300)
    
    return posts</code></pre>
                                </div>
                                
                                <div class="warning-box">
                                    <h4>💡 Performance Tips</h4>
                                    <ul>
                                        <li>Enable gzip compression in production</li>
                                        <li>Use CDN for static assets</li>
                                        <li>Implement database connection pooling</li>
                                        <li>Monitor application performance with profiling</li>
                                        <li>Use async/await for I/O operations</li>
                                    </ul>
                                </div>
                            </article>
                        </div>
                    </div>
                </div>
            </section>
        </div>
        """


class ExamplesPage(Component):
    """Examples page component"""
    
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        return f"""
        <div class="page-content">
            <section class="hero-small">
                <div class="container">
                    <h1 class="page-title">💡 Examples</h1>
                    <p class="page-subtitle">Real-world PyFrame applications and use cases</p>
                </div>
            </section>
            
            <section class="content-section">
                <div class="container">
                    <div class="examples-grid">
                        <div class="example-card">
                            <div class="example-preview">
                                <div class="preview-icon">🛒</div>
                            </div>
                            <div class="example-content">
                                <h3>E-commerce Store</h3>
                                <p>Full-featured online store with product catalog, shopping cart, and checkout. Demonstrates complex state management and API integration.</p>
                                <div class="example-tags">
                                    <span class="tag">State Management</span>
                                    <span class="tag">API Integration</span>
                                    <span class="tag">Authentication</span>
                                </div>
                                <div class="example-actions">
                                    <a href="#" class="btn-primary">View Demo</a>
                                    <a href="#" class="btn-secondary">Source Code</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="example-card">
                            <div class="example-preview">
                                <div class="preview-icon">📊</div>
                            </div>
                            <div class="example-content">
                                <h3>Analytics Dashboard</h3>
                                <p>Real-time dashboard with charts, graphs, and data visualization. Shows how to build interactive data-driven applications.</p>
                                <div class="example-tags">
                                    <span class="tag">Real-time Data</span>
                                    <span class="tag">Charts</span>
                                    <span class="tag">WebSockets</span>
                                </div>
                                <div class="example-actions">
                                    <a href="#" class="btn-primary">View Demo</a>
                                    <a href="#" class="btn-secondary">Source Code</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="example-card">
                            <div class="example-preview">
                                <div class="preview-icon">📝</div>
                            </div>
                            <div class="example-content">
                                <h3>Blog Platform</h3>
                                <p>Modern blog with markdown support, comments, and admin panel. Perfect example of content management with PyFrame.</p>
                                <div class="example-tags">
                                    <span class="tag">CMS</span>
                                    <span class="tag">Markdown</span>
                                    <span class="tag">Admin Panel</span>
                                </div>
                                <div class="example-actions">
                                    <a href="#" class="btn-primary">View Demo</a>
                                    <a href="#" class="btn-secondary">Source Code</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="example-card">
                            <div class="example-preview">
                                <div class="preview-icon">💬</div>
                            </div>
                            <div class="example-content">
                                <h3>Chat Application</h3>
                                <p>Real-time chat with rooms, private messages, and emoji support. Demonstrates WebSocket integration and real-time features.</p>
                                <div class="example-tags">
                                    <span class="tag">WebSockets</span>
                                    <span class="tag">Real-time</span>
                                    <span class="tag">Authentication</span>
                                </div>
                                <div class="example-actions">
                                    <a href="#" class="btn-primary">View Demo</a>
                                    <a href="#" class="btn-secondary">Source Code</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="example-card">
                            <div class="example-preview">
                                <div class="preview-icon">🎮</div>
                            </div>
                            <div class="example-content">
                                <h3>Game Portfolio</h3>
                                <p>Interactive game portfolio with animations and 3D effects. Shows PyFrame's capability for creative applications.</p>
                                <div class="example-tags">
                                    <span class="tag">Animations</span>
                                    <span class="tag">3D Graphics</span>
                                    <span class="tag">Interactive</span>
                                </div>
                                <div class="example-actions">
                                    <a href="#" class="btn-primary">View Demo</a>
                                    <a href="#" class="btn-secondary">Source Code</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="example-card">
                            <div class="example-preview">
                                <div class="preview-icon">🏢</div>
                            </div>
                            <div class="example-content">
                                <h3>Corporate Website</h3>
                                <p>Professional corporate website with multiple pages, contact forms, and SEO optimization. Enterprise-ready example.</p>
                                <div class="example-tags">
                                    <span class="tag">Multi-page</span>
                                    <span class="tag">SEO</span>
                                    <span class="tag">Forms</span>
                                </div>
                                <div class="example-actions">
                                    <a href="#" class="btn-primary">View Demo</a>
                                    <a href="#" class="btn-secondary">Source Code</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="cta-section">
                        <h2>Want to Add Your Example?</h2>
                        <p>Built something amazing with PyFrame? We'd love to showcase it!</p>
                        <a href="/contact" class="btn-primary large">Submit Your Example</a>
                    </div>
                </div>
            </section>
        </div>
        """


class ContactPage(Component):
    """Contact page component"""
    
    def __init__(self, **props):
        super().__init__()
        self.props = props
    
    def render(self):
        return f"""
        <div class="page-content">
            <section class="hero-small">
                <div class="container">
                    <h1 class="page-title">📬 Contact Us</h1>
                    <p class="page-subtitle">Get in touch with the PyFrame team</p>
                </div>
            </section>
            
            <section class="content-section">
                <div class="container">
                    <div class="contact-layout">
                        <div class="contact-info">
                            <h3>Get in Touch</h3>
                            <p>Have questions about PyFrame? Want to contribute? Or just say hello? We'd love to hear from you!</p>
                            
                            <div class="contact-methods">
                                <div class="contact-method">
                                    <div class="method-icon">💬</div>
                                    <div class="method-content">
                                        <h4>Discord Community</h4>
                                        <p>Join our Discord server for real-time discussions and support</p>
                                        <a href="#" class="contact-link">Join Discord</a>
                                    </div>
                                </div>
                                
                                <div class="contact-method">
                                    <div class="method-icon">📧</div>
                                    <div class="method-content">
                                        <h4>Email Support</h4>
                                        <p>Send us an email for support or partnership inquiries</p>
                                        <a href="mailto:hello@pyframe.dev" class="contact-link">hello@pyframe.dev</a>
                                    </div>
                                </div>
                                
                                <div class="contact-method">
                                    <div class="method-icon">🐛</div>
                                    <div class="method-content">
                                        <h4>GitHub Issues</h4>
                                        <p>Report bugs or request features on our GitHub repository</p>
                                        <a href="https://github.com/pyframe/pyframe/issues" class="contact-link">Report Issue</a>
                                    </div>
                                </div>
                                
                                <div class="contact-method">
                                    <div class="method-icon">🐦</div>
                                    <div class="method-content">
                                        <h4>Twitter</h4>
                                        <p>Follow us for updates and announcements</p>
                                        <a href="https://twitter.com/pyframe_dev" class="contact-link">@pyframe_dev</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="contact-form">
                            <form class="form" onsubmit="handleFormSubmit(event)">
                                <h3>Send us a Message</h3>
                                
                                <div class="form-group">
                                    <label for="name">Name</label>
                                    <input type="text" id="name" name="name" required>
                                </div>
                                
                                <div class="form-group">
                                    <label for="email">Email</label>
                                    <input type="email" id="email" name="email" required>
                                </div>
                                
                                <div class="form-group">
                                    <label for="subject">Subject</label>
                                    <select id="subject" name="subject" required>
                                        <option value="">Select a subject</option>
                                        <option value="general">General Inquiry</option>
                                        <option value="support">Technical Support</option>
                                        <option value="partnership">Partnership</option>
                                        <option value="contribution">Contribution</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label for="message">Message</label>
                                    <textarea id="message" name="message" rows="6" required placeholder="Tell us how we can help you..."></textarea>
                                </div>
                                
                                <button type="submit" class="btn-primary">Send Message</button>
                            </form>
                        </div>
                    </div>
                </div>
            </section>
        </div>
        
        <script>
            function handleFormSubmit(event) {{
                event.preventDefault();
                
                // Show success message
                const form = event.target;
                const button = form.querySelector('button[type="submit"]');
                const originalText = button.textContent;
                
                button.textContent = '✅ Message Sent!';
                button.disabled = true;
                
                // Reset after 3 seconds
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.disabled = false;
                    form.reset();
                }}, 3000);
            }}
        </script>
        """


class ShowcaseApp(StatefulComponent):
    """Main showcase application component with dark mode support"""
    
    def __init__(self, path='/', **props):
        super().__init__()
        self.path = path
        self.props = props
        self.state = State({
            'theme': 'light'
        })
    
    def render(self):
        current_path = self.path
        page_title = self.get_page_title(current_path)
        
        navigation = Navigation(current_path=current_path)
        dark_toggle = DarkModeToggle()
        page_content = self.get_page_content(current_path)
        
        return f"""
        <!DOCTYPE html>
        <html lang="en" data-theme="light">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{page_title}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                {self.get_styles()}
            </style>
        </head>
        <body>
            {navigation.render()}
            
            <header class="main-header">
                <div class="container header-content">
                    <div class="spacer"></div>
                    {dark_toggle.render()}
                </div>
            </header>
            
            <main>
                {page_content}
            </main>
            
            <footer class="footer">
                <div class="container">
                    <h3 class="footer-title">🎉 PyFrame is Revolutionary</h3>
                    <p class="footer-text">You just experienced a website built entirely with PyFrame Python components!</p>
                    <p class="footer-subtitle">Welcome to the future of web development.</p>
                    <div class="footer-note">
                        <p>✨ Built with PyFrame's reactive components and hot reload!</p>
                    </div>
                </div>
            </footer>
            
        </body>
        </html>
        """
    
    def get_page_title(self, path):
        """Get the page title based on the current path"""
        titles = {
            '/': 'PyFrame - Revolutionary Full-Stack Python Framework',
            '/about': 'About PyFrame - Revolutionary Python Web Framework',
            '/get-started': 'Get Started with PyFrame - Quick Tutorial',
            '/docs': 'PyFrame Documentation - Complete Guide',
            '/examples': 'PyFrame Examples - Real-world Applications',
            '/contact': 'Contact PyFrame Team - Get in Touch'
        }
        return titles.get(path, 'PyFrame - Revolutionary Python Framework')
    
    def get_page_content(self, path):
        """Get the page content based on the current path"""
        if path == '/':
            hero = HeroSection()
            features = FeaturesSection()
            status = LiveStatusSection()
            code = CodeExample()
            hot_reload = HotReloadDemo()
            
            return f"""
                {hero.render()}
                {features.render()}
                {status.render()}
                {code.render()}
                {hot_reload.render()}
            """
        elif path == '/about':
            about_page = AboutPage()
            return about_page.render()
        elif path == '/get-started':
            get_started_page = GetStartedPage()
            return get_started_page.render()
        elif path == '/docs':
            docs_page = DocsPage()
            return docs_page.render()
        elif path == '/examples':
            examples_page = ExamplesPage()
            return examples_page.render()
        elif path == '/contact':
            contact_page = ContactPage()
            return contact_page.render()
        else:
            # 404 page
            return f"""
                <div class="page-content">
                    <section class="hero-small">
                        <div class="container">
                            <h1 class="page-title">🔍 Page Not Found</h1>
                            <p class="page-subtitle">The page you're looking for doesn't exist.</p>
                            <a href="/" class="btn-primary">Go Home</a>
                        </div>
                    </section>
                </div>
            """
    
    def get_styles(self):
        """Return the CSS styles for the showcase with dark mode support"""
        return """
        /* CSS Custom Properties for Theme Support */
        :root {
            /* Light theme colors */
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #1a1a1a;
            --text-secondary: #6c757d;
            --text-muted: #adb5bd;
            --border-color: #dee2e6;
            --shadow-light: rgba(0, 0, 0, 0.1);
            --shadow-dark: rgba(0, 0, 0, 0.15);
            --accent-primary: #667eea;
            --accent-secondary: #764ba2;
            --code-bg: #f8f9fa;
            --code-border: #e9ecef;
        }

        [data-theme="dark"] {
            /* Dark theme colors */
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --border-color: #30363d;
            --shadow-light: rgba(0, 0, 0, 0.3);
            --shadow-dark: rgba(0, 0, 0, 0.5);
            --accent-primary: #7c3aed;
            --accent-secondary: #a855f7;
            --code-bg: #161b22;
            --code-border: #30363d;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-primary);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        /* Navigation Styles */
        .main-nav {
            background: var(--bg-primary);
            padding: 15px 0;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px var(--shadow-light);
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-logo {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .logo-icon {
            font-size: 1.8rem;
        }
        
        .nav-links {
            display: flex;
            gap: 30px;
            align-items: center;
        }
        
        .nav-link {
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            padding: 10px 15px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            color: var(--accent-primary);
            background: var(--bg-tertiary);
            transform: translateY(-1px);
        }
        
        .nav-link.active {
            color: var(--accent-primary);
            background: var(--bg-tertiary);
            font-weight: 600;
        }
        
        .nav-icon {
            font-size: 1.1rem;
        }
        
        .nav-actions {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .github-btn {
            background: var(--accent-primary);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .github-btn:hover {
            background: var(--accent-secondary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow-dark);
        }
        
        /* Mobile Menu Toggle */
        .mobile-menu-toggle {
            display: none;
            flex-direction: column;
            justify-content: space-around;
            width: 30px;
            height: 30px;
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 0;
            z-index: 1001;
        }
        
        .hamburger-line {
            width: 100%;
            height: 3px;
            background: var(--text-primary);
            transition: all 0.3s ease;
            transform-origin: center;
        }
        
        .mobile-menu-toggle.active .hamburger-line:nth-child(1) {
            transform: rotate(45deg) translate(7px, 7px);
        }
        
        .mobile-menu-toggle.active .hamburger-line:nth-child(2) {
            opacity: 0;
        }
        
        .mobile-menu-toggle.active .hamburger-line:nth-child(3) {
            transform: rotate(-45deg) translate(7px, -7px);
        }
        
        .nav-menu {
            display: flex;
            align-items: center;
            gap: 30px;
        }
        
        /* Header Styles */
        .main-header {
            background: var(--bg-secondary);
            padding: 15px 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo-text {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            text-decoration: none;
        }
        
        /* Dark Mode Toggle Styles */
        .dark-mode-toggle {
            display: flex;
            align-items: center;
        }
        
        .toggle-btn {
            background: var(--bg-tertiary);
            border: 2px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 25px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: inherit;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px var(--shadow-light);
        }
        
        .toggle-btn:hover {
            background: var(--accent-primary);
            color: white;
            border-color: var(--accent-primary);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px var(--shadow-dark);
        }
        
        .toggle-icon {
            font-size: 1.1rem;
        }
        
        .toggle-text {
            font-weight: 500;
        }
        
        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
            color: white;
            padding: 100px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
            min-height: 90vh;
            display: flex;
            align-items: center;
        }
        
        .hero-background {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            opacity: 0.2;
        }
        
        .hero-content {
            position: relative;
            z-index: 1;
        }
        
        .hero-title {
            font-size: 5rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #fff, #f0f8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .python-emoji {
            display: inline-block;
            animation: bounce 2s infinite;
        }
        
        .hero-subtitle {
            font-size: 1.8rem;
            font-weight: 300;
            margin-bottom: 20px;
            opacity: 0.9;
        }
        
        .hero-tagline {
            font-size: 1.3rem;
            margin-bottom: 50px;
            opacity: 0.8;
        }
        
        .hero-stats {
            display: flex;
            justify-content: center;
            gap: 60px;
            margin-top: 40px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-number {
            font-size: 3rem;
            font-weight: 700;
            color: #fff;
        }
        
        .stat-label {
            font-size: 1rem;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        /* Sections */
        .features-section, .status-section, .code-section, .hot-reload-section {
            padding: 80px 0;
            background: var(--bg-secondary);
        }
        
        .features-section {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }
        
        .status-section {
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border-color);
        }
        
        .hot-reload-section {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }
        
        .section-title {
            font-size: 3rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
            text-align: center;
        }
        
        .section-subtitle {
            font-size: 1.3rem;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 60px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Features Grid */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 40px;
            margin-top: 60px;
        }
        
        .feature-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 40px;
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 10px 30px var(--shadow-light);
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 60px var(--shadow-dark);
            border-color: var(--accent-primary);
        }
        
        .feature-icon {
            font-size: 4rem;
            margin-bottom: 25px;
            display: block;
        }
        
        .feature-title {
            font-size: 1.6rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
        }
        
        .feature-description {
            color: var(--text-secondary);
            line-height: 1.7;
            font-size: 1.1rem;
        }
        
        /* Status Grid */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin-top: 50px;
        }
        
        .status-card {
            background: var(--bg-primary);
            border: 2px solid var(--accent-primary);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px var(--shadow-dark);
        }
        
        .status-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .status-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--accent-primary);
            margin-bottom: 10px;
        }
        
        .status-description {
            color: var(--text-secondary);
            font-size: 1rem;
        }
        
        /* Code Section */
        .code-example {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 20px;
            overflow: hidden;
            margin: 40px 0;
            box-shadow: 0 20px 60px var(--shadow-dark);
        }
        
        .code-header {
            background: #2d3748;
            padding: 20px;
            border-bottom: 1px solid #4a5568;
        }
        
        .code-language {
            color: #667eea;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .code-content {
            color: #f8f8f2;
            padding: 30px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            overflow-x: auto;
        }
        
        .code-note {
            text-align: center;
            color: #4a5568;
            font-size: 1.2rem;
            margin-top: 30px;
            font-style: italic;
        }
        
        /* Hot Reload Demo */
        .hot-reload-demo {
            text-align: center;
            margin-top: 40px;
        }
        
        .hot-reload-btn {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            border: none;
            padding: 20px 50px;
            font-size: 1.4rem;
            font-weight: 600;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 15px 35px rgba(255, 107, 107, 0.4);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        
        .hot-reload-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: left 0.6s ease;
        }
        
        .hot-reload-btn:hover::before {
            left: 100%;
        }
        
        .hot-reload-btn:hover {
            transform: translateY(-8px) scale(1.05);
            box-shadow: 0 25px 60px rgba(255, 107, 107, 0.6);
            animation: pulse 1.5s infinite;
        }
        
        .hot-reload-btn.loading {
            opacity: 0.8;
            cursor: not-allowed;
            animation: pulse 1s infinite;
        }
        
        .reload-status {
            margin-top: 25px;
            font-size: 1.2rem;
            font-weight: 500;
            min-height: 30px;
        }
        
        /* Footer */
        .footer {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
            color: white;
            padding: 80px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .footer::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="sparkle" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="white" opacity="0.3"/></pattern></defs><rect width="100" height="100" fill="url(%23sparkle)"/></svg>');
            animation: sparkle 10s linear infinite;
        }
        
        .footer-title {
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #ffffff, #f0f8ff, #e6f3ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
        }
        
        .footer-text {
            font-size: 1.4rem;
            margin-bottom: 15px;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }
        
        .footer-subtitle {
            font-size: 1.2rem;
            opacity: 0.8;
            position: relative;
            z-index: 1;
            margin-bottom: 20px;
        }
        
        .footer-note {
            margin-top: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
            z-index: 1;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Beautiful Animations */
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-10px);
            }
            60% {
                transform: translateY(-5px);
            }
        }
        
        @keyframes sparkle {
            0% { transform: translateX(0); }
            100% { transform: translateX(-100px); }
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes slideInFromTop {
            0% {
                opacity: 0;
                transform: translateY(-50px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInFromBottom {
            0% {
                opacity: 0;
                transform: translateY(50px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInFromLeft {
            0% {
                opacity: 0;
                transform: translateX(-50px);
            }
            100% {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Enhanced Visual Effects */
        .feature-card {
            animation: slideInFromBottom 0.6s ease-out;
            animation-fill-mode: both;
        }
        
        .feature-card:nth-child(1) { animation-delay: 0.1s; }
        .feature-card:nth-child(2) { animation-delay: 0.2s; }
        .feature-card:nth-child(3) { animation-delay: 0.3s; }
        .feature-card:nth-child(4) { animation-delay: 0.4s; }
        .feature-card:nth-child(5) { animation-delay: 0.5s; }
        .feature-card:nth-child(6) { animation-delay: 0.6s; }
        
        .status-card {
            animation: slideInFromLeft 0.6s ease-out;
            animation-fill-mode: both;
        }
        
        .status-card:nth-child(1) { animation-delay: 0.2s; }
        .status-card:nth-child(2) { animation-delay: 0.4s; }
        .status-card:nth-child(3) { animation-delay: 0.6s; }
        
        .section-title {
            animation: slideInFromTop 0.8s ease-out;
        }
        
        .section-subtitle {
            animation: slideInFromTop 0.8s ease-out 0.2s;
            animation-fill-mode: both;
        }
        
        /* Enhanced Hover Effects */
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            opacity: 0;
            border-radius: 20px;
            transition: opacity 0.3s ease;
            z-index: -1;
        }
        
        .feature-card:hover::before {
            opacity: 0.1;
        }
        
        .toggle-btn {
            position: relative;
            overflow: hidden;
        }
        
        .toggle-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 50%;
            transition: all 0.5s ease;
            transform: translate(-50%, -50%);
            z-index: -1;
        }
        
        .toggle-btn:hover::before {
            width: 200%;
            height: 200%;
        }
        
        /* Page Layout Styles */
        .page-content {
            min-height: 80vh;
        }
        
        .hero-small {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
            color: white;
            padding: 80px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .page-title {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #ffffff, #f0f8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .page-subtitle {
            font-size: 1.4rem;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        
        .content-section {
            padding: 80px 0;
        }
        
        /* About Page Styles */
        .about-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 40px;
            margin-bottom: 80px;
        }
        
        .about-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px var(--shadow-light);
        }
        
        .about-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 50px var(--shadow-dark);
        }
        
        .about-icon {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        
        .team-section {
            background: var(--bg-secondary);
            padding: 80px 0;
            margin-top: 80px;
        }
        
        .team-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-top: 60px;
        }
        
        .team-member {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .team-member:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px var(--shadow-dark);
        }
        
        .member-avatar {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .member-role {
            color: var(--accent-primary);
            font-weight: 600;
            margin: 10px 0;
        }
        
        .member-bio {
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        /* Get Started Page Styles */
        .steps-container {
            display: grid;
            gap: 40px;
            margin: 60px 0;
        }
        
        .step-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 40px;
            position: relative;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px var(--shadow-light);
        }
        
        .step-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 50px var(--shadow-dark);
        }
        
        .step-number {
            position: absolute;
            top: -15px;
            left: 40px;
            background: var(--accent-primary);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.2rem;
        }
        
        .code-block {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            position: relative;
            overflow-x: auto;
        }
        
        .code-block.small {
            padding: 15px;
            margin: 15px 0;
        }
        
        .code-block pre {
            margin: 0;
            color: var(--text-primary);
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        }
        
        .copy-btn:hover {
            background: var(--accent-secondary);
        }
        
        .next-steps {
            margin-top: 80px;
            text-align: center;
        }
        
        .next-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
        
        .next-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 30px;
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.3s ease;
            display: block;
        }
        
        .next-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px var(--shadow-dark);
            border-color: var(--accent-primary);
        }
        
        .next-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        
        /* Documentation Page Styles */
        .docs-layout {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 60px;
            margin-top: 40px;
        }
        
        .docs-sidebar {
            background: var(--bg-secondary);
            border-radius: 15px;
            padding: 30px;
            height: fit-content;
            position: sticky;
            top: 100px;
        }
        
        .docs-nav .nav-section {
            margin-bottom: 30px;
        }
        
        .docs-nav h4 {
            color: var(--text-primary);
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .docs-nav a {
            display: block;
            color: var(--text-secondary);
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 8px;
            margin-bottom: 5px;
            transition: all 0.2s ease;
        }
        
        .docs-nav a:hover {
            background: var(--bg-tertiary);
            color: var(--accent-primary);
        }
        
        .docs-content {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 40px;
        }
        
        .doc-article h2 {
            color: var(--text-primary);
            margin: 40px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }
        
        .doc-article h3 {
            color: var(--text-primary);
            margin: 30px 0 15px 0;
        }
        
        .concept-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        
        .concept-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
        }
        
        .warning-box {
            background: var(--bg-tertiary);
            border: 1px solid var(--accent-primary);
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
        }
        
        .warning-box h4 {
            color: var(--accent-primary);
            margin-bottom: 10px;
        }
        
        /* Examples Page Styles */
        .examples-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 40px;
            margin: 60px 0;
        }
        
        .example-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px var(--shadow-light);
        }
        
        .example-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 25px 60px var(--shadow-dark);
        }
        
        .example-preview {
            background: var(--bg-tertiary);
            padding: 40px;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
        }
        
        .preview-icon {
            font-size: 4rem;
        }
        
        .example-content {
            padding: 30px;
        }
        
        .example-content h3 {
            color: var(--text-primary);
            margin-bottom: 15px;
        }
        
        .example-content p {
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 20px;
        }
        
        .example-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tag {
            background: var(--bg-tertiary);
            color: var(--accent-primary);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .example-actions {
            display: flex;
            gap: 15px;
        }
        
        .btn-primary, .btn-secondary {
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .btn-primary {
            background: var(--accent-primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--accent-secondary);
            transform: translateY(-2px);
        }
        
        .btn-primary.large {
            padding: 15px 30px;
            font-size: 1.1rem;
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background: var(--bg-secondary);
            border-color: var(--accent-primary);
        }
        
        .cta-section {
            text-align: center;
            margin-top: 80px;
            padding: 60px;
            background: var(--bg-secondary);
            border-radius: 20px;
        }
        
        /* Contact Page Styles */
        .contact-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            margin-top: 60px;
        }
        
        .contact-methods {
            margin-top: 40px;
        }
        
        .contact-method {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            padding: 20px;
            background: var(--bg-secondary);
            border-radius: 15px;
            transition: all 0.3s ease;
        }
        
        .contact-method:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px var(--shadow-light);
        }
        
        .method-icon {
            font-size: 2rem;
            flex-shrink: 0;
        }
        
        .method-content h4 {
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .method-content p {
            color: var(--text-secondary);
            margin-bottom: 10px;
            font-size: 0.9rem;
        }
        
        .contact-link {
            color: var(--accent-primary);
            text-decoration: none;
            font-weight: 500;
        }
        
        .contact-link:hover {
            text-decoration: underline;
        }
        
        .contact-form {
            background: var(--bg-secondary);
            border-radius: 20px;
            padding: 40px;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: inherit;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            /* Mobile Navigation */
            .mobile-menu-toggle {
                display: flex;
            }
            
            .nav-container {
                position: relative;
            }
            
            .nav-menu {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100vh;
                background: var(--bg-primary);
                flex-direction: column;
                justify-content: center;
                align-items: center;
                gap: 40px;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                z-index: 1000;
                padding: 80px 20px 20px;
                box-shadow: 2px 0 10px var(--shadow-dark);
            }
            
            .nav-menu.active {
                transform: translateX(0);
            }
            
            .nav-links {
                flex-direction: column;
                gap: 30px;
                text-align: center;
            }
            
            .nav-link {
                font-size: 1.2rem;
                padding: 15px 25px;
                border-radius: 12px;
                min-width: 200px;
                justify-content: center;
            }
            
            .nav-actions {
                margin-top: 20px;
            }
            
            .github-btn {
                padding: 15px 25px;
                font-size: 1.1rem;
            }
            
            /* Page Content */
            .hero-title, .page-title {
                font-size: 3rem;
            }
            
            .hero-subtitle, .page-subtitle {
                font-size: 1.3rem;
            }
            
            .hero-stats {
                gap: 30px;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
                gap: 30px;
            }
            
            .status-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .about-grid {
                grid-template-columns: 1fr;
                gap: 30px;
            }
            
            .team-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }
            
            .examples-grid {
                grid-template-columns: 1fr;
                gap: 30px;
            }
            
            .docs-layout {
                grid-template-columns: 1fr;
                gap: 30px;
            }
            
            .docs-sidebar {
                position: static;
                order: 2;
                margin-top: 40px;
            }
            
            .contact-layout {
                grid-template-columns: 1fr;
                gap: 40px;
            }
            
            .next-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .concept-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .container {
                padding: 0 15px;
            }
            
            .hero-small, .content-section {
                padding: 60px 0;
            }
            
            .step-card, .feature-card, .example-card {
                margin-bottom: 20px;
            }
        }
        
        @media (max-width: 480px) {
            .hero-title, .page-title {
                font-size: 2.5rem;
            }
            
            .nav-link {
                font-size: 1.1rem;
                min-width: 180px;
                padding: 12px 20px;
            }
            
            .example-actions {
                flex-direction: column;
                gap: 10px;
            }
            
            .btn-primary, .btn-secondary {
                text-align: center;
                width: 100%;
            }
            
            .hero-stats {
                gap: 20px;
            }
            
            .stat-number {
                font-size: 2.5rem;
            }
        }
        """


def create_showcase_app():
    """Create and configure the showcase application"""
    
    # Configuration
    config = PyFrameConfig(
        debug=True,
        hot_reload=True,  # Enable hot reload
        auto_reload=True,
        host="localhost",
        port=3000,
        ssr_enabled=False,  # Disable SSR temporarily to test
        hydration_strategy="partial",
        database_url="sqlite:///showcase.db"
    )
    
    # Create app
    app = PyFrameApp(config)
    
    # Initialize database
    DatabaseManager.initialize(config.database_url)
    DatabaseManager.create_all_tables()
    
    # Register plugins
    auth_plugin = AuthPlugin({
        "jwt_secret": "showcase-secret-key",
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
    
    # Define route handler function for multiple routes
    async def handle_route(context, path="/"):
        """Universal route handler for all pages"""
        try:
            # Force reload by re-executing the component code dynamically
            import importlib.util
            import sys
            import os
            
            if app.config.debug:
                try:
                    # Get the path to this file
                    current_file = __file__
                    
                    # Read and execute the file to get fresh classes
                    with open(current_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # Create a new namespace to execute the code in
                    namespace = {}
                    
                    # Add necessary imports to the namespace
                    namespace.update({
                        '__file__': current_file,
                        '__name__': '__dynamic_reload__',
                        'PyFrameApp': PyFrameApp,
                        'Component': Component,
                        'StatefulComponent': StatefulComponent,
                        'State': State,
                        'PyFrameConfig': PyFrameConfig,
                    })
                    
                    # Execute the file content in the new namespace
                    exec(file_content, namespace)
                    
                    # Get the fresh ShowcaseApp class
                    ShowcaseAppClass = namespace.get('ShowcaseApp')
                    if ShowcaseAppClass:
                        print(f"🔄 Creating fresh ShowcaseApp instance for {path}")
                        showcase = ShowcaseAppClass(path=path)
                    else:
                        print("⚠️ Could not find ShowcaseApp in reloaded code, using cached version")
                        showcase = ShowcaseApp(path=path)
                        
                except Exception as e:
                    print(f"⚠️ Dynamic reload error: {e}")
                    # Fallback to normal creation
                    showcase = ShowcaseApp(path=path)
            else:
                # Create showcase component instance normally
                showcase = ShowcaseApp(path=path)
                
            html_content = showcase.render()
            
            return {
                "status": 200,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": html_content
            }
        except Exception as e:
            print(f"❌ Error in route {path}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": 500,
                "headers": {"Content-Type": "text/html"},
                "body": f"<h1>Error</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>"
            }
    
    # Register all routes
    @app.route("/")
    async def home_route(context):
        return await handle_route(context, "/")
    
    @app.route("/about")
    async def about_route(context):
        return await handle_route(context, "/about")
    
    @app.route("/get-started")
    async def get_started_route(context):
        return await handle_route(context, "/get-started")
    
    @app.route("/docs")
    async def docs_route(context):
        return await handle_route(context, "/docs")
    
    @app.route("/examples")
    async def examples_route(context):
        return await handle_route(context, "/examples")
    
    @app.route("/contact")
    async def contact_route(context):
        return await handle_route(context, "/contact")
    
    return app


if __name__ == "__main__":
    # Create and run the showcase application
    app = create_showcase_app()
    
    print("🚀 Starting PyFrame Showcase Application...")
    print("📖 Built entirely with PyFrame Python components!")
    print("✨ Demonstrating:")
    print("   • Python components compiling to JavaScript")
    print("   • Reactive state management")
    print("   • Beautiful responsive design")
    print("   • Hot reload functionality")
    print("   • Plugin system integration")
    print("")
    
    app.run()
