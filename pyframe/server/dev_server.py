"""
Development Server

Fast development server with hot module replacement, file watching,
and debugging tools for PyFrame applications.
"""

import asyncio
import os
import sys
import json
import websockets
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import importlib.util
import traceback

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    """Handles file system changes for hot reload"""
    
    def __init__(self, dev_server: 'DevServer'):
        self.dev_server = dev_server
        self.ignored_patterns = {'.pyc', '__pycache__', '.git', '.vscode', 'node_modules'}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Ignore certain file types and directories
        if any(pattern in str(file_path) for pattern in self.ignored_patterns):
            return
            
        if file_path.suffix in ['.py', '.html', '.css', '.js']:
            print(f"File changed: {file_path}")
            asyncio.create_task(self.dev_server.handle_file_change(str(file_path)))


class DevServerWebSocket:
    """WebSocket connection for dev server communication"""
    
    def __init__(self, websocket, dev_server: 'DevServer'):
        self.websocket = websocket
        self.dev_server = dev_server
        
    async def send_reload_signal(self):
        """Send reload signal to client"""
        try:
            message = {
                "type": "reload",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending reload signal: {e}")
            
    async def send_error(self, error_info: Dict[str, Any]):
        """Send error information to client"""
        try:
            message = {
                "type": "error",
                "error": error_info,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending error info: {e}")
            
    async def send_log(self, log_data: Dict[str, Any]):
        """Send log data to client"""
        try:
            message = {
                "type": "log",
                "log": log_data,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending log: {e}")


class DevServer:
    """
    Development server with hot reload and debugging capabilities.
    
    Provides file watching, automatic reloading, error reporting,
    and debugging tools for PyFrame applications.
    """
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
        
        # Server state
        self.is_running = False
        self.file_observer: Optional[Observer] = None
        self.websocket_clients: List[DevServerWebSocket] = []
        
        # Error tracking
        self.last_error: Optional[Dict[str, Any]] = None
        self.error_count = 0
        
        # Performance monitoring
        self.request_times: List[float] = []
        self.component_render_times: Dict[str, List[float]] = {}
        
    async def start(self):
        """Start the development server"""
        
        self.is_running = True
        
        # Start file watcher
        if self.config.hot_reload:
            await self._start_file_watcher()
            
        # Start WebSocket server for hot reload
        if self.config.hot_reload:
            await self._start_websocket_server()
            
        # Start main HTTP server
        await self._start_http_server()
        
    async def stop(self):
        """Stop the development server"""
        
        self.is_running = False
        
        # Stop file watcher
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            
        # Close WebSocket connections
        for client in self.websocket_clients:
            try:
                await client.websocket.close()
            except:
                pass
                
        self.websocket_clients.clear()
        
    async def _start_file_watcher(self):
        """Start file system watcher"""
        
        if not self.config.auto_reload:
            return
            
        event_handler = FileChangeHandler(self)
        self.file_observer = Observer()
        
        # Watch current directory and subdirectories
        watch_path = os.getcwd()
        self.file_observer.schedule(event_handler, watch_path, recursive=True)
        self.file_observer.start()
        
        print(f"File watcher started for {watch_path}")
        
    async def _start_websocket_server(self):
        """Start WebSocket server for hot reload communication"""
        
        async def websocket_handler(websocket, path):
            client = DevServerWebSocket(websocket, self)
            self.websocket_clients.append(client)
            
            print(f"Hot reload client connected: {websocket.remote_address}")
            
            try:
                await websocket.wait_closed()
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                if client in self.websocket_clients:
                    self.websocket_clients.remove(client)
                    
        # Start WebSocket server on port + 1
        ws_port = self.config.port + 1
        start_server = websockets.serve(websocket_handler, self.config.host, ws_port)
        await start_server
        
        print(f"Hot reload WebSocket server started on {self.config.host}:{ws_port}")
        
    async def _start_http_server(self):
        """Start HTTP server with request handling"""
        
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class PyFrameRequestHandler(BaseHTTPRequestHandler):
            def __init__(self, dev_server, *args, **kwargs):
                self.dev_server = dev_server
                super().__init__(*args, **kwargs)
                
            def do_GET(self):
                self._handle_request("GET")
                
            def do_POST(self):
                self._handle_request("POST")
                
            def do_PUT(self):
                self._handle_request("PUT")
                
            def do_DELETE(self):
                self._handle_request("DELETE")
                
            def _handle_request(self, method):
                try:
                    import time
                    
                    # Start timing
                    start_time = time.time()
                    
                    # Prepare request data
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else None
                    
                    request_data = {
                        "method": method,
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body": body
                    }
                    
                    # Handle hot reload injection for HTML responses
                    if self.path == "/__pyframe_dev__/hot-reload.js":
                        self._serve_hot_reload_script()
                        return
                        
                    # Process request through PyFrame app
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        response = loop.run_until_complete(
                            self.dev_server.app.handle_request(request_data)
                        )
                        
                        # Record timing
                        end_time = time.time()
                        request_time = end_time - start_time
                        self.dev_server.request_times.append(request_time)
                        
                        # Keep only last 100 timings
                        if len(self.dev_server.request_times) > 100:
                            self.dev_server.request_times = self.dev_server.request_times[-100:]
                            
                        # Send response
                        self._send_response(response)
                        
                    except Exception as e:
                        self.dev_server._handle_error(e)
                        self._send_error_response(e)
                    finally:
                        # Clean up the event loop
                        loop.close()
                        
                except Exception as e:
                    print(f"Request handling error: {e}")
                    self._send_error_response(e)
                    
            def _serve_hot_reload_script(self):
                """Serve hot reload JavaScript"""
                
                script = f"""
// PyFrame Hot Reload Script
(function() {{
    const ws = new WebSocket('ws://{self.dev_server.config.host}:{self.dev_server.config.port + 1}');
    
    ws.onopen = function() {{
        console.log('🔥 PyFrame hot reload connected');
    }};
    
    ws.onmessage = function(event) {{
        const message = JSON.parse(event.data);
        
        switch(message.type) {{
            case 'reload':
                console.log('🔄 Reloading page...');
                location.reload();
                break;
                
            case 'error':
                console.error('❌ PyFrame Error:', message.error);
                showErrorOverlay(message.error);
                break;
                
            case 'log':
                console.log('📝 PyFrame Log:', message.log);
                break;
        }}
    }};
    
    ws.onclose = function() {{
        console.log('🔌 Hot reload disconnected - attempting reconnection...');
        setTimeout(() => location.reload(), 1000);
    }};
    
    function showErrorOverlay(error) {{
        // Remove existing overlay
        const existing = document.getElementById('pyframe-error-overlay');
        if (existing) existing.remove();
        
        // Create error overlay
        const overlay = document.createElement('div');
        overlay.id = 'pyframe-error-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            font-family: monospace;
            padding: 20px;
            z-index: 999999;
            overflow: auto;
        `;
        
        overlay.innerHTML = `
            <h2 style="color: #ff6b6b;">PyFrame Development Error</h2>
            <p><strong>Type:</strong> ${{error.type}}</p>
            <p><strong>Message:</strong> ${{error.message}}</p>
            <pre style="background: #333; padding: 10px; border-radius: 4px; overflow: auto;">
${{error.traceback}}
            </pre>
            <button onclick="this.parentElement.remove()" 
                    style="padding: 10px 20px; margin-top: 10px; background: #007acc; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Close
            </button>
        `;
        
        document.body.appendChild(overlay);
    }}
}})();
"""
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                self.send_header('Content-Length', str(len(script)))
                self.end_headers()
                self.wfile.write(script.encode('utf-8'))
                
            def _send_response(self, response):
                """Send PyFrame response"""
                
                status = response.get('status', 200)
                headers = response.get('headers', {})
                body = response.get('body', '')
                
                # Inject hot reload script for HTML responses
                if (headers.get('Content-Type', '').startswith('text/html') and 
                    self.dev_server.config.hot_reload):
                    body = self._inject_hot_reload_script(body)
                    
                self.send_response(status)
                
                # Send headers
                for key, value in headers.items():
                    self.send_header(key, value)
                    
                # Update content length if modified
                if isinstance(body, str):
                    body_bytes = body.encode('utf-8')
                    self.send_header('Content-Length', str(len(body_bytes)))
                    self.end_headers()
                    self.wfile.write(body_bytes)
                else:
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    
            def _inject_hot_reload_script(self, html_body):
                """Inject hot reload script into HTML"""
                
                if '</body>' in html_body:
                    script_tag = f'<script src="/__pyframe_dev__/hot-reload.js"></script></body>'
                    html_body = html_body.replace('</body>', script_tag)
                elif '</html>' in html_body:
                    script_tag = f'<script src="/__pyframe_dev__/hot-reload.js"></script></html>'
                    html_body = html_body.replace('</html>', script_tag)
                    
                return html_body
                
            def _send_error_response(self, error):
                """Send error response"""
                
                error_html = f"""
                <html>
                <head><title>PyFrame Development Error</title></head>
                <body>
                    <h1>Development Error</h1>
                    <p><strong>Error:</strong> {str(error)}</p>
                    <pre>{traceback.format_exc()}</pre>
                </body>
                </html>
                """
                
                self.send_response(500)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(error_html)))
                self.end_headers()
                self.wfile.write(error_html.encode('utf-8'))
                
            def log_message(self, format, *args):
                """Override to customize logging"""
                if self.dev_server.config.debug:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] {format % args}")
                    
        # Create partial class with dev_server bound
        def handler_factory(*args, **kwargs):
            return PyFrameRequestHandler(self, *args, **kwargs)
            
        # Start server in background thread
        def run_server():
            server = HTTPServer((self.config.host, self.config.port), handler_factory)
            server.serve_forever()
            
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        print(f"PyFrame development server started at http://{self.config.host}:{self.config.port}")
        
        # Keep event loop running
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()
            
    async def handle_file_change(self, file_path: str):
        """Handle file system change"""
        
        print(f"Handling file change: {file_path}")
        
        try:
            # Reload Python modules if needed
            if file_path.endswith('.py'):
                await self._reload_python_modules(file_path)
                
            # Notify clients to reload
            await self._notify_clients_reload()
            
        except Exception as e:
            await self._handle_error(e)
            
    async def _reload_python_modules(self, file_path: str):
        """Reload Python modules"""
        
        # Simple module reloading - in practice this would be more sophisticated
        # and handle dependencies between modules
        
        try:
            # Convert file path to module name
            rel_path = os.path.relpath(file_path)
            if rel_path.startswith('pyframe/'):
                module_name = rel_path.replace('/', '.').replace('.py', '')
                
                # Reload if already imported
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    print(f"Reloaded module: {module_name}")
                    
        except Exception as e:
            print(f"Error reloading module: {e}")
            
    async def _notify_clients_reload(self):
        """Notify all connected clients to reload"""
        
        for client in self.websocket_clients:
            await client.send_reload_signal()
            
    def _handle_error(self, error: Exception):
        """Handle development error"""
        
        self.error_count += 1
        
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat(),
            "count": self.error_count
        }
        
        self.last_error = error_info
        
        # Notify clients of error
        asyncio.create_task(self._notify_clients_error(error_info))
        
        print(f"Development Error #{self.error_count}: {error}")
        
    async def _notify_clients_error(self, error_info: Dict[str, Any]):
        """Notify clients of error"""
        
        for client in self.websocket_clients:
            await client.send_error(error_info)
            
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information"""
        
        avg_request_time = (
            sum(self.request_times) / len(self.request_times) 
            if self.request_times else 0
        )
        
        return {
            "server_status": "running" if self.is_running else "stopped",
            "connected_clients": len(self.websocket_clients),
            "total_requests": len(self.request_times),
            "average_request_time": round(avg_request_time * 1000, 2),  # ms
            "error_count": self.error_count,
            "last_error": self.last_error,
            "hot_reload_enabled": self.config.hot_reload,
            "file_watcher_active": self.file_observer is not None and self.file_observer.is_alive()
        }
