"""
Authentication Plugin

Provides user authentication, session management, and authorization
capabilities with support for multiple authentication backends.
"""

import jwt
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

from .plugin import Plugin, PluginInfo, HookType
from ..data.models import Model, Field, FieldType


@dataclass
class UserSession:
    """Represents a user session"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
        
    def extend(self, duration: timedelta) -> None:
        """Extend session expiration"""
        self.expires_at = datetime.now() + duration


class AuthUser(Model):
    """Default user model for authentication"""
    
    username: str = Field(FieldType.STRING, unique=True, max_length=50)
    email: str = Field(FieldType.EMAIL, unique=True)
    password_hash: str = Field(FieldType.STRING, max_length=255)
    first_name: str = Field(FieldType.STRING, max_length=50, required=False)
    last_name: str = Field(FieldType.STRING, max_length=50, required=False)
    is_active: bool = Field(FieldType.BOOLEAN, default=True)
    is_staff: bool = Field(FieldType.BOOLEAN, default=False)
    is_superuser: bool = Field(FieldType.BOOLEAN, default=False)
    last_login: Optional[datetime] = Field(FieldType.DATETIME, required=False)
    date_joined: datetime = Field(FieldType.DATETIME, auto_now_add=True)
    
    def check_password(self, password: str) -> bool:
        """Check if password matches"""
        return self._hash_password(password) == self.password_hash
        
    def set_password(self, password: str) -> None:
        """Set user password"""
        self.password_hash = self._hash_password(password)
        
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using secure algorithm"""
        # In production, use bcrypt, scrypt, or argon2
        salt = "pyframe_salt"  # Should be random per user
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()


class AuthBackend:
    """Base authentication backend interface"""
    
    async def authenticate(self, username: str, password: str) -> Optional[AuthUser]:
        """Authenticate user credentials"""
        raise NotImplementedError
        
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID"""
        raise NotImplementedError


class DatabaseAuthBackend(AuthBackend):
    """Database-based authentication backend"""
    
    async def authenticate(self, username: str, password: str) -> Optional[AuthUser]:
        """Authenticate against database"""
        try:
            # Try username or email
            user = AuthUser.get(username=username) or AuthUser.get(email=username)
            
            if user and user.is_active and user.check_password(password):
                user.last_login = datetime.now()
                user.save()
                return user
                
        except Exception as e:
            print(f"Authentication error: {e}")
            
        return None
        
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID"""
        try:
            return AuthUser.get(id=user_id)
        except Exception:
            return None


class JWTAuthBackend(AuthBackend):
    """JWT-based authentication backend"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        
    async def authenticate(self, token: str) -> Optional[AuthUser]:
        """Authenticate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if user_id:
                return await self.get_user(user_id)
                
        except jwt.InvalidTokenError:
            pass
            
        return None
        
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID"""
        try:
            return AuthUser.get(id=user_id)
        except Exception:
            return None
            
    def create_token(self, user: AuthUser, expires_delta: timedelta = None) -> str:
        """Create JWT token for user"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
            
        payload = {
            "user_id": str(user.id),
            "username": user.username,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class AuthPlugin(Plugin):
    """
    Authentication plugin providing user management and session handling.
    
    Features:
    - Multiple authentication backends
    - Session management
    - Permission and role system
    - Password security
    - JWT token support
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        self.backends: List[AuthBackend] = []
        self.sessions: Dict[str, UserSession] = {}
        self.jwt_backend: Optional[JWTAuthBackend] = None
        
        # Configuration
        self.session_timeout = timedelta(hours=24)
        self.jwt_secret = self.get_config("jwt_secret", "your-secret-key")
        self.jwt_algorithm = self.get_config("jwt_algorithm", "HS256")
        self.password_min_length = self.get_config("password_min_length", 8)
        self.require_email_verification = self.get_config("require_email_verification", False)
        
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="auth",
            version="1.0.0",
            description="Authentication and authorization plugin",
            author="PyFrame Team",
            dependencies=[],
            tags=["authentication", "security", "users"]
        )
        
    async def initialize(self, app) -> None:
        """Initialize authentication plugin"""
        
        # Setup default backend
        db_backend = DatabaseAuthBackend()
        self.backends.append(db_backend)
        
        # Setup JWT backend if configured
        if self.jwt_secret:
            self.jwt_backend = JWTAuthBackend(self.jwt_secret, self.jwt_algorithm)
            self.backends.append(self.jwt_backend)
            
        # Register hooks
        self.register_hook(HookType.BEFORE_REQUEST, self._authenticate_request, priority=10)
        self.register_hook(HookType.AFTER_REQUEST, self._update_session, priority=90)
        
        # Create auth routes
        self._setup_auth_routes(app)
        
        # Start session cleanup task
        asyncio.create_task(self._session_cleanup_task())
        
        print("Authentication plugin initialized")
        
    def _setup_auth_routes(self, app) -> None:
        """Setup authentication routes"""
        
        @app.route("/auth/login", methods=["POST"])
        async def login(context):
            return await self.handle_login(context)
            
        @app.route("/auth/logout", methods=["POST"])
        async def logout(context):
            return await self.handle_logout(context)
            
        @app.route("/auth/register", methods=["POST"])
        async def register(context):
            return await self.handle_register(context)
            
        @app.route("/auth/profile", methods=["GET"])
        async def profile(context):
            return await self.handle_profile(context)
            
        @app.route("/auth/change-password", methods=["POST"])
        async def change_password(context):
            return await self.handle_change_password(context)
            
    async def _authenticate_request(self, context: Dict[str, Any], *args, **kwargs) -> None:
        """Authenticate incoming request"""
        request_context = kwargs.get("request_context")
        if not request_context:
            return
            
        user = None
        session = None
        
        # Check for session cookie
        session_id = self._get_session_id_from_request(request_context)
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.is_expired():
                user = await self._get_user_by_id(session.user_id)
                if user:
                    session.extend(self.session_timeout)
                    
        # Check for JWT token
        if not user:
            token = self._get_jwt_token_from_request(request_context)
            if token and self.jwt_backend:
                user = await self.jwt_backend.authenticate(token)
                
        # Store in context
        context["user"] = user
        context["session"] = session
        context["is_authenticated"] = user is not None
        
    async def _update_session(self, context: Dict[str, Any], *args, **kwargs) -> None:
        """Update session after request"""
        session = context.get("session")
        if session and not session.is_expired():
            # Session is still valid, no action needed
            pass
            
    async def _session_cleanup_task(self) -> None:
        """Periodic task to clean up expired sessions"""
        while True:
            try:
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if session.is_expired()
                ]
                
                for session_id in expired_sessions:
                    del self.sessions[session_id]
                    
                if expired_sessions:
                    print(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Session cleanup error: {e}")
                await asyncio.sleep(60)
                
    def _get_session_id_from_request(self, request_context) -> Optional[str]:
        """Extract session ID from request"""
        # Check cookies
        cookies = request_context.headers.get("cookie", "")
        for cookie in cookies.split(";"):
            if "sessionid=" in cookie:
                return cookie.split("sessionid=")[1].strip()
        return None
        
    def _get_jwt_token_from_request(self, request_context) -> Optional[str]:
        """Extract JWT token from request"""
        # Check Authorization header
        auth_header = request_context.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None
        
    async def _get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID using backends"""
        for backend in self.backends:
            user = await backend.get_user(user_id)
            if user:
                return user
        return None
        
    async def authenticate(self, username: str, password: str) -> Optional[AuthUser]:
        """Authenticate user credentials"""
        for backend in self.backends:
            if hasattr(backend, 'authenticate'):
                user = await backend.authenticate(username, password)
                if user:
                    return user
        return None
        
    def create_session(self, user: AuthUser, request_context) -> UserSession:
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        
        session = UserSession(
            session_id=session_id,
            user_id=str(user.id),
            created_at=datetime.now(),
            expires_at=datetime.now() + self.session_timeout,
            ip_address=request_context.headers.get("x-forwarded-for") or 
                      request_context.headers.get("remote-addr"),
            user_agent=request_context.headers.get("user-agent")
        )
        
        self.sessions[session_id] = session
        return session
        
    def destroy_session(self, session_id: str) -> bool:
        """Destroy user session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
        
    def create_jwt_token(self, user: AuthUser, expires_delta: timedelta = None) -> str:
        """Create JWT token for user"""
        if not self.jwt_backend:
            raise ValueError("JWT backend not configured")
        return self.jwt_backend.create_token(user, expires_delta)
        
    async def handle_login(self, context) -> Dict[str, Any]:
        """Handle login request"""
        try:
            import json
            
            # Parse request body
            if not context.body:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Request body required"})
                }
                
            data = json.loads(context.body)
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Username and password required"})
                }
                
            # Authenticate user
            user = await self.authenticate(username, password)
            
            if not user:
                return {
                    "status": 401,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Invalid credentials"})
                }
                
            # Create session and JWT token
            session = self.create_session(user, context)
            jwt_token = self.create_jwt_token(user)
            
            response_data = {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                },
                "token": jwt_token,
                "session_id": session.session_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Set-Cookie": f"sessionid={session.session_id}; Path=/; HttpOnly; SameSite=Lax"
            }
            
            return {
                "status": 200,
                "headers": headers,
                "body": json.dumps(response_data)
            }
            
        except Exception as e:
            return {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }
            
    async def handle_logout(self, context) -> Dict[str, Any]:
        """Handle logout request"""
        try:
            import json
            
            # Get session ID
            session_id = self._get_session_id_from_request(context)
            
            if session_id:
                self.destroy_session(session_id)
                
            headers = {
                "Content-Type": "application/json",
                "Set-Cookie": "sessionid=; Path=/; HttpOnly; Max-Age=0"
            }
            
            return {
                "status": 200,
                "headers": headers,
                "body": json.dumps({"message": "Logged out successfully"})
            }
            
        except Exception as e:
            return {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }
            
    async def handle_register(self, context) -> Dict[str, Any]:
        """Handle user registration"""
        try:
            import json
            
            if not context.body:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Request body required"})
                }
                
            data = json.loads(context.body)
            
            # Validate required fields
            required_fields = ["username", "email", "password"]
            for field in required_fields:
                if not data.get(field):
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": f"{field} is required"})
                    }
                    
            # Validate password
            if len(data["password"]) < self.password_min_length:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": f"Password must be at least {self.password_min_length} characters"})
                }
                
            # Check if user exists
            if AuthUser.get(username=data["username"]) or AuthUser.get(email=data["email"]):
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "User already exists"})
                }
                
            # Create user
            user = AuthUser(
                username=data["username"],
                email=data["email"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", "")
            )
            user.set_password(data["password"])
            user.save()
            
            response_data = {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                },
                "message": "User created successfully"
            }
            
            return {
                "status": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response_data)
            }
            
        except Exception as e:
            return {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }
            
    async def handle_profile(self, context) -> Dict[str, Any]:
        """Handle profile request"""
        try:
            import json
            
            # Check authentication
            user = context.get("user")
            if not user:
                return {
                    "status": 401,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Authentication required"})
                }
                
            user_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined.isoformat() if user.date_joined else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(user_data)
            }
            
        except Exception as e:
            return {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }
            
    async def handle_change_password(self, context) -> Dict[str, Any]:
        """Handle password change request"""
        try:
            import json
            
            # Check authentication
            user = context.get("user")
            if not user:
                return {
                    "status": 401,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Authentication required"})
                }
                
            if not context.body:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Request body required"})
                }
                
            data = json.loads(context.body)
            current_password = data.get("current_password")
            new_password = data.get("new_password")
            
            if not current_password or not new_password:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Current and new password required"})
                }
                
            # Verify current password
            if not user.check_password(current_password):
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Current password is incorrect"})
                }
                
            # Validate new password
            if len(new_password) < self.password_min_length:
                return {
                    "status": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": f"Password must be at least {self.password_min_length} characters"})
                }
                
            # Update password
            user.set_password(new_password)
            user.save()
            
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Password changed successfully"})
            }
            
        except Exception as e:
            return {
                "status": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }


# Authentication decorators and utilities

def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a route"""
    
    def wrapper(*args, **kwargs):
        context = kwargs.get("context")
        if context and not context.get("is_authenticated"):
            import json
            return {
                "status": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Authentication required"})
            }
        return func(*args, **kwargs)
        
    return wrapper


def require_staff(func: Callable) -> Callable:
    """Decorator to require staff privileges"""
    
    def wrapper(*args, **kwargs):
        context = kwargs.get("context")
        user = context.get("user") if context else None
        
        if not user or not user.is_staff:
            import json
            return {
                "status": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Staff privileges required"})
            }
            
        return func(*args, **kwargs)
        
    return wrapper


def require_superuser(func: Callable) -> Callable:
    """Decorator to require superuser privileges"""
    
    def wrapper(*args, **kwargs):
        context = kwargs.get("context")
        user = context.get("user") if context else None
        
        if not user or not user.is_superuser:
            import json
            return {
                "status": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Superuser privileges required"})
            }
            
        return func(*args, **kwargs)
        
    return wrapper
