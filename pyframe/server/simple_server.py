"""
Simple HTTP Server for PyFrame Development

A simplified development server that actually works without complex asyncio threading issues.
"""

import asyncio
import importlib
import json
import os
import sys
import threading
import time
import traceback
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Set
from urllib.parse import parse_qs, urlparse
from pathlib import Path

# Import file watching dependencies
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. File watching disabled.")


class SimpleFileChangeHandler(FileSystemEventHandler):
    """Handles file system changes for hot reload in SimpleDevServer"""
    
    def __init__(self, dev_server):
        self.dev_server = dev_server
        self.ignored_patterns = {'.pyc', '__pycache__', '.git', '.vscode', 'node_modules', '.db'}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Ignore certain file types and directories
        if any(pattern in str(file_path) for pattern in self.ignored_patterns):
            return
            
        if file_path.suffix in ['.py', '.html', '.css', '.js']:
            print(f"🔥 File changed: {file_path}")
            
            # Reload Python modules if it's a .py file
            if file_path.suffix == '.py':
                self._reload_python_module(file_path)
            
            # Schedule hot reload in the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.dev_server.trigger_reload())
                else:
                    # If no loop is running, run in new loop
                    asyncio.run(self.dev_server.trigger_reload())
            except RuntimeError:
                # Fallback: run in new event loop
                asyncio.run(self.dev_server.trigger_reload())
    
    def _reload_python_module(self, file_path):
        """Reload a Python module that has changed"""
        try:
            # Convert file path to module name
            rel_path = os.path.relpath(file_path)
            
            # Handle main.py specially - just log it, the route handler will handle reloading
            if rel_path.endswith('main.py'):
                print("🔄 main.py changed - will reload on next request")
                return
            
            # Convert path to module name for importable modules
            if rel_path.startswith('pyframe/'):
                module_name = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')
                
                # Reload if already imported
                if module_name in sys.modules:
                    print(f"🔄 Reloading module: {module_name}")
                    importlib.reload(sys.modules[module_name])
                else:
                    print(f"🔄 Module not yet imported: {module_name}")
                    
        except Exception as e:
            print(f"⚠️ Error reloading module: {e}")


class SimpleHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for PyFrame development"""
    
    def __init__(self, app, dev_server, *args, **kwargs):
        self.app = app
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
    
    def _handle_request(self, method: str):
        """Handle HTTP request"""
        try:
            # Parse request
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = None
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
            
            # Create request data
            request_data = {
                "method": method,
                "path": path,
                "query": query_params,
                "headers": dict(self.headers),
                "body": body
            }
            
            # Handle special dev server routes
            if path == "/__pyframe_dev__/hot-reload.js":
                self._serve_hot_reload_script()
                return
            elif path == "/__pyframe_dev__/status":
                self._serve_status()
                return
            elif path == "/__pyframe_dev__/reload":
                self._trigger_reload()
                return
            
            # Handle request through PyFrame app
            response = self._process_request(request_data)
            self._send_response(response)
            
        except Exception as e:
            print(f"❌ Request error: {e}")
            traceback.print_exc()
            self._send_error_response(str(e))
    
    def _process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through PyFrame app"""
        try:
            # For now, always use synchronous fallback to avoid async complexity
            # In a production PyFrame, this would be more sophisticated
            print("Using synchronous fallback for all requests")
            return self._process_request_sync(request_data)
                    
        except Exception as e:
            print(f"❌ App processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": 500,
                "headers": {"Content-Type": "text/html"},
                "body": f"""
                <html>
                <head><title>PyFrame Error</title></head>
                <body>
                    <h1>Internal Server Error</h1>
                    <p>Error: {e}</p>
                    <pre>{traceback.format_exc()}</pre>
                </body>
                </html>
                """
            }
    
    def _process_request_sync(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process request synchronously by using the PyFrame app's routing system"""
        try:
            path = request_data.get("path", "/")
            print(f"🔄 Processing request through PyFrame app: {path}")
            
            # Try to use the PyFrame app's routing system
            try:
                # Create a new event loop for this request
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Process through the PyFrame app
                response = loop.run_until_complete(self.app.handle_request(request_data))
                loop.close()
                
                return response
                
            except Exception as e:
                print(f"🔄 PyFrame routing failed, using fallback: {e}")
                # Fallback content if PyFrame routing fails
                return self._get_fallback_content(path)

                
        except Exception as e:
            print(f"❌ Sync processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": 500,
                "headers": {"Content-Type": "text/html"},
                "body": f"<h1>Error</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>"
            }
    
    def _get_fallback_content(self, path: str) -> Dict[str, Any]:
        """Get fallback content when PyFrame routing fails"""
        if path.startswith("/api/"):
            # Simple API response
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": '{"message": "PyFrame API working!", "framework": "PyFrame", "language": "Python"}'
            }
        else:
            # Simple fallback HTML
            return {
                "status": 200,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>PyFrame Development Server</title>
                </head>
                <body>
                    <h1>🐍 PyFrame Development Server</h1>
                    <p>No routes registered. Add routes to your PyFrame app to see content here.</p>
                </body>
                </html>
                """
            }
    
    def _send_response(self, response: Dict[str, Any]):
        """Send HTTP response"""
        status = response.get("status", 200)
        headers = response.get("headers", {})
        body = response.get("body", "")
        
        # Convert body to bytes if it's a string with proper UTF-8 encoding
        if isinstance(body, str):
            body = body.encode('utf-8', errors='replace')
        
        # Send status
        self.send_response(status)
        
        # Send headers
        for key, value in headers.items():
            self.send_header(key, value)
        
        # Add hot reload script injection for HTML responses (only if hot reload is enabled)
        if headers.get("Content-Type", "").startswith("text/html") and self.dev_server.config.hot_reload:
            if isinstance(body, bytes):
                body_str = body.decode('utf-8')
            else:
                body_str = str(body)
                
            # Inject hot reload script before closing body tag
            if "</body>" in body_str:
                hot_reload_script = '''
                <script src="/__pyframe_dev__/hot-reload.js"></script>
                '''
                body_str = body_str.replace("</body>", f"{hot_reload_script}</body>")
                body = body_str.encode('utf-8')
        
        # Send content length
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        
        # Send body
        self.wfile.write(body)
    
    def _send_error_response(self, error_msg: str):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        error_html = f"""
        <html>
        <head><title>PyFrame Error</title></head>
        <body>
            <h1>Development Error</h1>
            <p><strong>Error:</strong> {error_msg}</p>
            <p><em>This error occurred during development. Fix the issue and the page will reload automatically.</em></p>
            <script src="/__pyframe_dev__/hot-reload.js"></script>
        </body>
        </html>
        """
        self.wfile.write(error_html.encode('utf-8'))
    
    def _serve_hot_reload_script(self):
        """Serve hot reload JavaScript"""
        script = """// PyFrame Hot Reload Script
(function() {
    console.log('🔥 PyFrame hot reload script loaded');
    
    let ws = null;
    let reconnectInterval = 1000;
    let maxReconnectAttempts = 5;
    let reconnectAttempts = 0;
    
    function connect() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            console.log('🔥 PyFrame hot reload: Max reconnection attempts reached. Hot reload disabled.');
            return;
        }
        
        try {
            const wsPort = location.port ? parseInt(location.port) + 1 : 8001;
            ws = new WebSocket('ws://localhost:' + wsPort);
            
            ws.onopen = function() {
                console.log('🔥 PyFrame hot reload connected');
                reconnectInterval = 1000;
                reconnectAttempts = 0;
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'reload') {
                        console.log('🔥 Hot reload triggered');
                        location.reload();
                    }
                } catch (e) {
                    console.log('🔥 Hot reload: Invalid message received');
                }
            };
            
            ws.onclose = function() {
                reconnectAttempts++;
                if (reconnectAttempts < maxReconnectAttempts) {
                    console.log('🔥 Hot reload disconnected, attempting reconnect... (' + reconnectAttempts + '/' + maxReconnectAttempts + ')');
                    setTimeout(connect, reconnectInterval);
                    reconnectInterval = Math.min(reconnectInterval * 1.2, 5000);
                } else {
                    console.log('🔥 Hot reload disabled (WebSocket server not available)');
                }
            };
            
            ws.onerror = function() {
                // Don't spam console with errors, just close
                if (ws) {
                    ws.close();
                }
            };
            
        } catch (e) {
            reconnectAttempts++;
            if (reconnectAttempts < maxReconnectAttempts) {
                setTimeout(connect, reconnectInterval);
            }
        }
    }
    
    // Only try to connect if we're in development mode
    if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
        connect();
    } else {
        console.log('🔥 Hot reload disabled (not in development mode)');
    }
})();"""
        
        script_bytes = script.encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript; charset=utf-8')
        self.send_header('Content-Length', str(len(script_bytes)))
        self.end_headers()
        self.wfile.write(script_bytes)
    
    def _serve_status(self):
        """Serve development server status"""
        status = {
            "status": "running",
            "framework": "PyFrame",
            "timestamp": time.time()
        }
        
        response = json.dumps(status)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def _trigger_reload(self):
        """Trigger hot reload manually"""
        try:
            # Trigger reload via the dev server
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.dev_server.reload())
            loop.close()
            
            response = json.dumps({
                "message": "Hot reload triggered successfully", 
                "timestamp": time.time(),
                "clients": len(self.dev_server.ws_clients)
            })
        except Exception as e:
            response = json.dumps({
                "message": f"Hot reload error: {e}", 
                "timestamp": time.time()
            })
            
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"🌐 {self.address_string()} - {format % args}")


class SimpleDevServer:
    """Simple development server for PyFrame applications"""
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.server = None
        self.ws_server = None
        self.ws_clients: Set = set()
        self.running = False
        self.file_observer = None
    
    async def _websocket_handler(self, websocket, path):
        """Handle WebSocket connections for hot reload"""
        self.ws_clients.add(websocket)
        print(f"🔥 Hot reload client connected (total: {len(self.ws_clients)})")
        
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.discard(websocket)
            print(f"🔥 Hot reload client disconnected (total: {len(self.ws_clients)})")
    
    async def _handle_websocket_connection(self, *args):
        """Handle WebSocket connection with flexible signature"""
        # Handle different websockets library versions
        if len(args) == 1:
            # Modern websockets (v11+): only websocket argument
            websocket = args[0]
            path = getattr(websocket, 'path', '/')
        elif len(args) == 2:
            # Older websockets: websocket and path arguments
            websocket, path = args
        else:
            print(f"🔥 Unexpected WebSocket handler arguments: {args}")
            return
        
        return await self._websocket_handler(websocket, path)
    
    async def _start_websocket_server(self):
        """Start the WebSocket server for hot reload"""
        ws_port = self.config.port + 1
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                # Use a simple direct handler approach
                self.ws_server = await websockets.serve(
                    self._handle_websocket_connection,
                    self.config.host,
                    ws_port + attempt
                )
                print(f"   🔥 WebSocket server: ws://{self.config.host}:{ws_port + attempt}")
                return
            except OSError as e:
                if attempt == max_attempts - 1:
                    print(f"   ⚠️  Warning: Could not start WebSocket server after {max_attempts} attempts")
                    print(f"   🔥 Hot reload will be disabled")
                    self.ws_server = None
                    return
                else:
                    print(f"   🔄 Port {ws_port + attempt} in use, trying {ws_port + attempt + 1}...")
    
    def _start_http_server(self):
        """Start HTTP server in a separate thread"""
        def handler_factory(*args, **kwargs):
            return SimpleHTTPHandler(self.app, self, *args, **kwargs)
        
        self.server = HTTPServer((self.config.host, self.config.port), handler_factory)
        self.server.serve_forever()
    
    async def start(self):
        """Start the development server"""
        try:
            print(f"🚀 Starting PyFrame dev server...")
            print(f"   📍 Host: {self.config.host}")
            print(f"   🔌 Port: {self.config.port}")
            print(f"   🌐 URL: http://{self.config.host}:{self.config.port}")
            
            # Start WebSocket server for hot reload
            await self._start_websocket_server()
            if self.ws_server:
                print(f"   🔥 Hot reload: enabled")
            else:
                print(f"   🔥 Hot reload: disabled (WebSocket server failed)")
            
            # Start file watcher for hot reload
            if self.config.hot_reload and WATCHDOG_AVAILABLE:
                self._start_file_watcher()
                print(f"   📁 File watcher: enabled")
            else:
                print(f"   📁 File watcher: disabled")
            
            print()
            
            self.running = True
            
            print("✅ PyFrame server is running!")
            print("   Press Ctrl+C to stop")
            print()
            
            # Start HTTP server in a separate thread
            http_thread = threading.Thread(target=self._start_http_server, daemon=True)
            http_thread.start()
            
            # Keep the event loop running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down PyFrame server...")
            self.stop()
        except Exception as e:
            print(f"❌ Server error: {e}")
            traceback.print_exc()
    
    def _start_file_watcher(self):
        """Start file system watcher"""
        if not WATCHDOG_AVAILABLE:
            return
            
        event_handler = SimpleFileChangeHandler(self)
        self.file_observer = Observer()
        
        # Watch current directory and subdirectories
        watch_path = os.getcwd()
        self.file_observer.schedule(event_handler, watch_path, recursive=True)
        self.file_observer.start()
        
        print(f"   👀 Watching: {watch_path}")
    
    async def trigger_reload(self):
        """Trigger hot reload by sending WebSocket messages to connected clients"""
        if not self.ws_server:
            print("🔥 Hot reload triggered (WebSocket server not available)")
            return
            
        if not self.ws_clients:
            print("🔥 Hot reload triggered (no clients connected)")
            return
            
        print(f"🔥 Hot reload triggered, notifying {len(self.ws_clients)} client(s)")
        
        message = json.dumps({"type": "reload", "timestamp": time.time()})
        
        # Send reload message to all connected clients
        disconnected_clients = set()
        for client in self.ws_clients:
            try:
                await client.send(message)
            except Exception as e:
                print(f"🔥 Failed to send reload to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.ws_clients -= disconnected_clients
    
    def stop(self):
        """Stop the development server"""
        self.running = False
        
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            
        if self.ws_server:
            self.ws_server.close()
            
        print("✅ PyFrame server stopped")
