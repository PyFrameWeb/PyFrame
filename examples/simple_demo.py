"""
PyFrame Simple Demo

A minimal example showing the core PyFrame features without complex server setup.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for PyFrame imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# PyFrame imports
from pyframe.core.component import Component, StatefulComponent
from pyframe.data.models import Model, Field, FieldType
from pyframe.data.database import DatabaseManager
from pyframe.compiler.transpiler import PythonToJSTranspiler


# Demo Model
class DemoPost(Model):
    """Simple post model for demo"""
    title: str = Field(FieldType.STRING, max_length=100)
    content: str = Field(FieldType.TEXT)
    published: bool = Field(FieldType.BOOLEAN, default=False)


# Demo Components
class SimpleCounter(StatefulComponent):
    """A simple counter component"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        self.set_state("count", 0)
        
    def increment(self):
        """Increment the counter"""
        count = self.get_state("count", 0)
        self.set_state("count", count + 1)
        print(f"Counter incremented to: {count + 1}")
        
    def render(self):
        """Render the counter component"""
        count = self.get_state("count", 0)
        return f"""
        <div class="counter">
            <h2>PyFrame Counter Demo</h2>
            <p>Current count: <strong>{count}</strong></p>
            <button onclick="this.component.increment()">
                Click to increment!
            </button>
            <p><em>This button would work in a browser with the compiled JavaScript!</em></p>
        </div>
        """


class PostList(StatefulComponent):
    """Component showing posts from database"""
    
    def __init__(self, props=None, children=None):
        super().__init__(props, children)
        
        # Load posts from database
        try:
            posts = DemoPost.all()
            posts_data = [post.to_dict() for post in posts]
        except:
            posts_data = []
            
        self.set_state("posts", posts_data)
        
    def render(self):
        """Render the post list"""
        posts = self.get_state("posts", [])
        
        if not posts:
            posts_html = "<p><em>No posts yet. Creating some sample data...</em></p>"
        else:
            posts_html = ""
            for post in posts:
                posts_html += f"""
                <div class="post">
                    <h3>{post['title']}</h3>
                    <p>{post['content'][:100]}...</p>
                    <small>Published: {post['published']}</small>
                </div>
                """
        
        return f"""
        <div class="post-list">
            <h2>PyFrame Data Layer Demo</h2>
            <p>Posts automatically loaded from database:</p>
            {posts_html}
        </div>
        """


def demo_compiler():
    """Demonstrate the Python-to-JS compiler"""
    print("\n🔧 PYTHON-TO-JS COMPILER DEMO")
    print("=" * 50)
    
    # Create a counter component
    counter = SimpleCounter()
    
    # Initialize the transpiler
    transpiler = PythonToJSTranspiler()
    
    # Compile the component to JavaScript
    try:
        result = transpiler.transpile_component(counter)
        
        print("✅ Python component successfully compiled to JavaScript!")
        print("\nGenerated JavaScript (first 500 chars):")
        print("-" * 40)
        print(result.js_code[:500] + "..." if len(result.js_code) > 500 else result.js_code)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Compilation error: {e}")


def demo_data_layer():
    """Demonstrate the data layer with auto-generated models"""
    print("\n📊 DATA LAYER DEMO")
    print("=" * 50)
    
    # Initialize database
    DatabaseManager.initialize("sqlite:///demo.db")
    DatabaseManager.create_all_tables()
    
    print("✅ Database initialized and tables created!")
    
    # Create some sample posts
    if not DemoPost.all():
        posts_data = [
            {
                "title": "Welcome to PyFrame",
                "content": "PyFrame allows you to write full-stack applications entirely in Python!",
                "published": True
            },
            {
                "title": "Reactive Components",
                "content": "Build interactive UIs with Python components that compile to JavaScript.",
                "published": True
            },
            {
                "title": "Zero-Boilerplate Data",
                "content": "Define models with Python classes and get automatic APIs and migrations.",
                "published": False
            }
        ]
        
        for post_data in posts_data:
            post = DemoPost.create(**post_data)
            print(f"✅ Created post: {post.title}")
    
    # Query the data
    all_posts = DemoPost.all()
    published_posts = DemoPost.filter(published=True)
    
    print(f"\n📈 Database Statistics:")
    print(f"   • Total posts: {len(all_posts)}")
    print(f"   • Published posts: {len(published_posts)}")
    
    # Show model serialization
    if all_posts:
        first_post = all_posts[0]
        print(f"\n🔄 Model Serialization:")
        print(f"   • to_dict(): {first_post.to_dict()}")
        print(f"   • to_json(): {first_post.to_json()}")


def demo_components():
    """Demonstrate reactive components"""
    print("\n⚛️  REACTIVE COMPONENTS DEMO")
    print("=" * 50)
    
    # Create and test counter component
    counter = SimpleCounter()
    print("✅ Counter component created!")
    
    print("\n🎨 Initial render:")
    print(counter.render())
    
    print("\n🔄 Testing state changes:")
    counter.increment()  # Should print "Counter incremented to: 1"
    counter.increment()  # Should print "Counter incremented to: 2"
    counter.increment()  # Should print "Counter incremented to: 3"
    
    print("\n🎨 Render after state changes:")
    print(counter.render())
    
    # Create and test post list component
    print("\n📝 Creating post list component...")
    post_list = PostList()
    print("✅ Post list component created!")
    
    print("\n🎨 Post list render:")
    print(post_list.render())


def demo_runtime_js():
    """Demonstrate runtime JavaScript generation"""
    print("\n🌐 RUNTIME JAVASCRIPT DEMO")
    print("=" * 50)
    
    transpiler = PythonToJSTranspiler()
    
    # Generate the runtime JavaScript
    runtime_js = transpiler.generate_runtime_js()
    polyfills_js = transpiler.generate_polyfills_js()
    
    print("✅ Generated PyFrame runtime JavaScript!")
    print(f"   • Runtime size: {len(runtime_js)} characters")
    print(f"   • Polyfills size: {len(polyfills_js)} characters")
    
    print("\n💡 The runtime includes:")
    print("   • Reactive state management")
    print("   • Component lifecycle handling")
    print("   • Event binding and DOM updates")
    print("   • Python-like utility functions")


def main():
    """Run all demos"""
    print("🐍 PyFrame Framework Demo")
    print("🚀 Full-Stack Python Web Framework")
    print("=" * 50)
    print()
    print("This demo showcases PyFrame's core features:")
    print("✨ Write frontend components in Python")
    print("🔧 Automatic compilation to JavaScript")
    print("📊 Zero-boilerplate data layer")
    print("⚛️  Reactive state management")
    print("🌐 Context-aware rendering")
    print()
    
    try:
        # Run all the demos
        demo_data_layer()
        demo_components() 
        demo_compiler()
        demo_runtime_js()
        
        print("\n" + "=" * 50)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print()
        print("📖 What you just saw:")
        print("   ✅ Python models automatically creating database tables")
        print("   ✅ Reactive components with state management")
        print("   ✅ Python code compiling to JavaScript")
        print("   ✅ Full runtime system generation")
        print()
        print("🚀 In a real PyFrame app, this would all happen automatically!")
        print("   • Components would render in the browser")
        print("   • State changes would update the UI live")
        print("   • APIs would be auto-generated for your models")
        print("   • Everything would be optimized for your users")
        print()
        print("🔗 Try the full blog demo: python examples/blog_app/main.py")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
