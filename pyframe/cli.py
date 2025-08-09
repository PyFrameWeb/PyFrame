"""
PyFrame Command Line Interface

Provides commands for creating new projects, running development servers,
and managing PyFrame applications.
"""

import click
import os
import shutil
from pathlib import Path

@click.group()
@click.version_option(version="0.1.0", prog_name="PyFrame")
def main():
    """PyFrame - Revolutionary Full-Stack Python Web Framework"""
    pass

@main.command()
@click.argument('project_name')
@click.option('--template', '-t', default='basic', 
              help='Project template (basic, blog, dashboard)')
@click.option('--directory', '-d', default='.', 
              help='Directory to create project in')
def create(project_name, template, directory):
    """Create a new PyFrame project"""
    project_path = Path(directory) / project_name
    
    if project_path.exists():
        click.echo(f"❌ Error: Directory '{project_path}' already exists!")
        return
    
    # Create project directory
    project_path.mkdir(parents=True)
    
    # Create basic project structure
    create_basic_project(project_path, project_name, template)
    
    click.echo(f"✅ Created PyFrame project '{project_name}' in {project_path}")
    click.echo(f"")
    click.echo(f"Next steps:")
    click.echo(f"  cd {project_name}")
    click.echo(f"  pip install -r requirements.txt")
    click.echo(f"  python main.py")
    click.echo(f"")
    click.echo(f"🚀 Your app will be available at http://localhost:3000")

def create_basic_project(project_path, project_name, template):
    """Create a basic PyFrame project structure"""
    
    # Create main.py
    main_py = f'''"""
{project_name} - A PyFrame Application
"""

from pyframe import PyFrameApp, Component, PyFrameConfig

class HomePage(Component):
    def render(self):
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{project_name}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    text-align: center;
                    max-width: 600px;
                }}
                h1 {{
                    font-size: 3rem;
                    margin-bottom: 1rem;
                }}
                p {{
                    font-size: 1.2rem;
                    margin-bottom: 2rem;
                    opacity: 0.9;
                }}
                .cta {{
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    display: inline-block;
                    transition: all 0.3s ease;
                }}
                .cta:hover {{
                    background: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🐍 Welcome to {project_name}!</h1>
                <p>Your PyFrame application is up and running.</p>
                <p>Edit <code>main.py</code> to get started building your app.</p>
                <a href="https://github.com/PyFrameWeb/PyFrame" class="cta">📚 Read the Docs</a>
            </div>
        </body>
        </html>
        """

def create_app():
    """Create and configure the PyFrame application"""
    config = PyFrameConfig(
        debug=True,
        hot_reload=True,
        host="localhost",
        port=3000
    )
    
    app = PyFrameApp(config)
    
    @app.route("/")
    async def home(context):
        page = HomePage()
        return {{
            "status": 200,
            "headers": {{"Content-Type": "text/html; charset=utf-8"}},
            "body": page.render()
        }}
    
    return app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting {project_name}...")
    print("📍 Running at http://localhost:3000")
    print("🔥 Hot reload enabled")
    print("Press Ctrl+C to stop")
    app.run()
'''
    
    (project_path / "main.py").write_text(main_py, encoding='utf-8')
    
    # Create requirements.txt
    requirements = '''pyframe>=0.1.0
# Add your additional dependencies here
'''
    (project_path / "requirements.txt").write_text(requirements, encoding='utf-8')
    
    # Create README.md
    readme = f'''# {project_name}

A [PyFrame](https://pyframe.dev) application.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   python main.py
   ```

3. Open your browser to [http://localhost:3000](http://localhost:3000)

## Project Structure

- `main.py` - Main application file
- `requirements.txt` - Python dependencies

## Learn More

- [PyFrame Documentation](https://github.com/PyFrameWeb/PyFrame/blob/main/README.md)
- [PyFrame Examples](https://github.com/PyFrameWeb/PyFrame/tree/main/examples)
- [PyFrame GitHub](https://github.com/PyFrameWeb/PyFrame)

## Built with PyFrame

This application is built with [PyFrame](https://github.com/PyFrameWeb/PyFrame) - the revolutionary full-stack Python web framework that lets you write React-like components in pure Python.
'''
    (project_path / "README.md").write_text(readme, encoding='utf-8')

@main.command()
@click.option('--host', default='localhost', help='Host to bind to')
@click.option('--port', default=3000, help='Port to bind to')
@click.option('--debug/--no-debug', default=True, help='Enable debug mode')
@click.option('--hot-reload/--no-hot-reload', default=True, help='Enable hot reload')
def run(host, port, debug, hot_reload):
    """Run the PyFrame development server"""
    if not os.path.exists('main.py'):
        click.echo("❌ Error: No main.py found in current directory")
        click.echo("Run 'pyframe create <project_name>' to create a new project")
        return
    
    click.echo(f"🚀 Starting PyFrame development server...")
    click.echo(f"📍 Running at http://{host}:{port}")
    click.echo(f"🔥 Hot reload: {'enabled' if hot_reload else 'disabled'}")
    click.echo(f"🐛 Debug mode: {'enabled' if debug else 'disabled'}")
    click.echo(f"Press Ctrl+C to stop")
    
    # Import and run the user's app
    try:
        import main
        if hasattr(main, 'create_app'):
            app = main.create_app()
        elif hasattr(main, 'app'):
            app = main.app
        else:
            click.echo("❌ Error: No 'create_app()' function or 'app' variable found in main.py")
            return
        
        app.config.host = host
        app.config.port = port
        app.config.debug = debug
        app.config.hot_reload = hot_reload
        
        app.run()
    except ImportError as e:
        click.echo(f"❌ Error importing main.py: {e}")
    except Exception as e:
        click.echo(f"❌ Error running application: {e}")

@main.command()
def version():
    """Show PyFrame version"""
    click.echo("PyFrame 0.1.0")
    click.echo("🐍 Revolutionary Full-Stack Python Web Framework")
    click.echo("🌐 https://github.com/PyFrameWeb/PyFrame")

if __name__ == '__main__':
    main()
