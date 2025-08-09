"""
Request Context and Client Detection

Automatically detects client context including device type, network quality,
user preferences, and geographic location for adaptive rendering.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import parse_qs, urlparse
from enum import Enum


class DeviceType(Enum):
    """Device type categories"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    TV = "tv"
    BOT = "bot"
    UNKNOWN = "unknown"


class ConnectionType(Enum):
    """Network connection types"""
    FAST = "fast"        # WiFi, Ethernet, 4G+
    MODERATE = "moderate"  # 3G, slower connections
    SLOW = "slow"        # 2G, very slow
    OFFLINE = "offline"  # No connection
    UNKNOWN = "unknown"


@dataclass
class ClientContext:
    """
    Represents client context information for adaptive rendering.
    
    Automatically detected from request headers and client hints.
    """
    
    # Device information
    device_type: DeviceType = DeviceType.UNKNOWN
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    pixel_ratio: float = 1.0
    touch_enabled: bool = False
    
    # Network information
    connection_type: ConnectionType = ConnectionType.UNKNOWN
    downlink: Optional[float] = None  # Mbps
    rtt: Optional[int] = None  # Round trip time in ms
    save_data: bool = False
    
    # User preferences
    prefers_dark_mode: bool = False
    prefers_reduced_motion: bool = False
    prefers_reduced_transparency: bool = False
    language: str = "en"
    timezone: Optional[str] = None
    
    # Browser capabilities
    browser_name: str = "unknown"
    browser_version: str = "unknown"
    supports_webp: bool = False
    supports_avif: bool = False
    supports_js: bool = True
    supports_service_worker: bool = False
    
    # Location (if available)
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    
    # Performance hints
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    
    def is_mobile(self) -> bool:
        """Check if client is mobile device"""
        return self.device_type in [DeviceType.MOBILE, DeviceType.TABLET]
        
    def is_low_end_device(self) -> bool:
        """Check if client appears to be low-end device"""
        if self.memory_gb and self.memory_gb < 2:
            return True
        if self.cpu_cores and self.cpu_cores < 2:
            return True
        if self.connection_type in [ConnectionType.SLOW, ConnectionType.MODERATE]:
            return True
        return False
        
    def should_optimize_images(self) -> bool:
        """Check if images should be optimized for this client"""
        return (
            self.save_data or 
            self.connection_type in [ConnectionType.SLOW, ConnectionType.MODERATE] or
            self.is_low_end_device()
        )
        
    def get_preferred_image_format(self) -> str:
        """Get preferred image format for this client"""
        if self.supports_avif:
            return "avif"
        elif self.supports_webp:
            return "webp"
        else:
            return "jpg"
            
    def should_reduce_animations(self) -> bool:
        """Check if animations should be reduced"""
        return (
            self.prefers_reduced_motion or
            self.save_data or
            self.is_low_end_device()
        )


@dataclass
class RequestContext:
    """
    Complete request context including HTTP details and client context.
    
    Provides all information needed for adaptive rendering and response generation.
    """
    
    # HTTP request details
    method: str = "GET"
    path: str = "/"
    query_params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    
    # Parsed path parameters (from routing)
    path_params: Dict[str, str] = field(default_factory=dict)
    
    # Client context
    client_context: ClientContext = field(default_factory=ClientContext)
    
    # Response details (set during processing)
    response: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_request(cls, request_data: Dict[str, Any]) -> 'RequestContext':
        """Create RequestContext from raw request data"""
        
        context = cls(
            method=request_data.get("method", "GET"),
            path=request_data.get("path", "/"),
            headers=request_data.get("headers", {}),
            body=request_data.get("body")
        )
        
        # Parse query parameters
        parsed_url = urlparse(context.path)
        context.path = parsed_url.path
        context.query_params = parse_qs(parsed_url.query)
        
        # Flatten single-item lists in query params
        for key, value in context.query_params.items():
            if isinstance(value, list) and len(value) == 1:
                context.query_params[key] = value[0]
                
        # Detect client context
        context.client_context = ClientContextDetector.detect(context.headers)
        
        return context
        
    def get_title(self) -> str:
        """Get page title based on path"""
        # Simple title generation - could be more sophisticated
        if self.path == "/":
            return "PyFrame App"
        else:
            path_parts = self.path.strip("/").split("/")
            title = " ".join(part.title() for part in path_parts)
            return f"{title} - PyFrame App"
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "method": self.method,
            "path": self.path,
            "query_params": self.query_params,
            "path_params": self.path_params,
            "client_context": {
                "device_type": self.client_context.device_type.value,
                "connection_type": self.client_context.connection_type.value,
                "prefers_dark_mode": self.client_context.prefers_dark_mode,
                "prefers_reduced_motion": self.client_context.prefers_reduced_motion,
                "language": self.client_context.language,
                "is_mobile": self.client_context.is_mobile(),
                "should_optimize_images": self.client_context.should_optimize_images()
            }
        }


class ClientContextDetector:
    """
    Detects client context from request headers and client hints.
    
    Uses various heuristics to determine device capabilities and user preferences.
    """
    
    # User agent patterns for device detection
    MOBILE_PATTERNS = [
        r'Mobile', r'Android', r'iPhone', r'iPad', r'BlackBerry', 
        r'Windows Phone', r'Opera Mini'
    ]
    
    TABLET_PATTERNS = [
        r'iPad', r'Android.*Tablet', r'Windows.*Touch'
    ]
    
    TV_PATTERNS = [
        r'Smart-?TV', r'GoogleTV', r'AppleTV', r'NetCast', r'BRAVIA'
    ]
    
    BOT_PATTERNS = [
        r'bot', r'crawler', r'spider', r'scraper', r'slurp', r'facebook'
    ]
    
    # Browser detection patterns
    BROWSER_PATTERNS = {
        'chrome': r'Chrome/(\d+)',
        'firefox': r'Firefox/(\d+)',
        'safari': r'Safari/(\d+)',
        'edge': r'Edge/(\d+)',
        'opera': r'Opera/(\d+)'
    }
    
    @classmethod
    def detect(cls, headers: Dict[str, str]) -> ClientContext:
        """Detect client context from request headers"""
        
        context = ClientContext()
        
        # Normalize header keys (case-insensitive lookup)
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        
        # Detect device type and browser from User-Agent
        user_agent = normalized_headers.get('user-agent', '')
        context.device_type = cls._detect_device_type(user_agent)
        context.browser_name, context.browser_version = cls._detect_browser(user_agent)
        
        # Client Hints (modern browsers)
        cls._process_client_hints(context, normalized_headers)
        
        # Network information
        cls._process_network_hints(context, normalized_headers)
        
        # User preferences
        cls._process_user_preferences(context, normalized_headers)
        
        # Accept headers for capability detection
        cls._process_accept_headers(context, normalized_headers)
        
        # Language detection
        accept_language = normalized_headers.get('accept-language', 'en')
        context.language = cls._parse_language(accept_language)
        
        return context
        
    @classmethod
    def _detect_device_type(cls, user_agent: str) -> DeviceType:
        """Detect device type from User-Agent"""
        
        if not user_agent:
            return DeviceType.UNKNOWN
            
        # Check for bots first
        for pattern in cls.BOT_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return DeviceType.BOT
                
        # Check for TV
        for pattern in cls.TV_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return DeviceType.TV
                
        # Check for tablet (before mobile, as tablets often contain "Mobile")
        for pattern in cls.TABLET_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return DeviceType.TABLET
                
        # Check for mobile
        for pattern in cls.MOBILE_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return DeviceType.MOBILE
                
        return DeviceType.DESKTOP
        
    @classmethod
    def _detect_browser(cls, user_agent: str) -> Tuple[str, str]:
        """Detect browser name and version from User-Agent"""
        
        for browser, pattern in cls.BROWSER_PATTERNS.items():
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                version = match.group(1) if match.groups() else "unknown"
                return browser, version
                
        return "unknown", "unknown"
        
    @classmethod
    def _process_client_hints(cls, context: ClientContext, headers: Dict[str, str]) -> None:
        """Process Client Hints headers"""
        
        # Viewport width/height
        if 'sec-ch-viewport-width' in headers:
            try:
                context.screen_width = int(headers['sec-ch-viewport-width'])
            except ValueError:
                pass
                
        if 'sec-ch-viewport-height' in headers:
            try:
                context.screen_height = int(headers['sec-ch-viewport-height'])
            except ValueError:
                pass
                
        # Device pixel ratio
        if 'sec-ch-dpr' in headers:
            try:
                context.pixel_ratio = float(headers['sec-ch-dpr'])
            except ValueError:
                pass
                
        # Mobile hint
        if 'sec-ch-ua-mobile' in headers:
            context.touch_enabled = headers['sec-ch-ua-mobile'] == '?1'
            
        # Platform (can help with device detection)
        platform = headers.get('sec-ch-ua-platform', '').strip('"').lower()
        if platform in ['android', 'ios']:
            if context.device_type == DeviceType.UNKNOWN:
                context.device_type = DeviceType.MOBILE
                
        # CPU cores
        if 'sec-ch-ua-platform-version' in headers:
            # This is a simplified example - real detection would be more complex
            pass
            
    @classmethod
    def _process_network_hints(cls, context: ClientContext, headers: Dict[str, str]) -> None:
        """Process Network Information API headers"""
        
        # Save-Data header
        if 'save-data' in headers:
            context.save_data = headers['save-data'].lower() == 'on'
            
        # Downlink (effective bandwidth)
        if 'downlink' in headers:
            try:
                context.downlink = float(headers['downlink'])
                
                # Categorize connection type based on downlink
                if context.downlink >= 10:
                    context.connection_type = ConnectionType.FAST
                elif context.downlink >= 1.5:
                    context.connection_type = ConnectionType.MODERATE
                else:
                    context.connection_type = ConnectionType.SLOW
                    
            except ValueError:
                pass
                
        # Round Trip Time
        if 'rtt' in headers:
            try:
                context.rtt = int(headers['rtt'])
            except ValueError:
                pass
                
        # Effective Connection Type
        ect = headers.get('ect', '').lower()
        if ect:
            ect_mapping = {
                'slow-2g': ConnectionType.SLOW,
                '2g': ConnectionType.SLOW,
                '3g': ConnectionType.MODERATE,
                '4g': ConnectionType.FAST
            }
            context.connection_type = ect_mapping.get(ect, ConnectionType.UNKNOWN)
            
    @classmethod
    def _process_user_preferences(cls, context: ClientContext, headers: Dict[str, str]) -> None:
        """Process user preference headers"""
        
        # Dark mode preference
        color_scheme = headers.get('sec-ch-prefers-color-scheme', '')
        context.prefers_dark_mode = color_scheme == 'dark'
        
        # Reduced motion preference
        reduced_motion = headers.get('sec-ch-prefers-reduced-motion', '')
        context.prefers_reduced_motion = reduced_motion == 'reduce'
        
        # Reduced transparency
        reduced_transparency = headers.get('sec-ch-prefers-reduced-transparency', '')
        context.prefers_reduced_transparency = reduced_transparency == 'reduce'
        
    @classmethod
    def _process_accept_headers(cls, context: ClientContext, headers: Dict[str, str]) -> None:
        """Process Accept headers for capability detection"""
        
        # Image format support
        accept = headers.get('accept', '').lower()
        context.supports_webp = 'image/webp' in accept
        context.supports_avif = 'image/avif' in accept
        
        # JavaScript support (assume true unless explicitly disabled)
        # This is hard to detect from headers alone
        context.supports_js = True
        
    @classmethod
    def _parse_language(cls, accept_language: str) -> str:
        """Parse primary language from Accept-Language header"""
        
        if not accept_language:
            return "en"
            
        # Parse Accept-Language header (e.g., "en-US,en;q=0.9,es;q=0.8")
        languages = []
        for lang_spec in accept_language.split(','):
            lang_spec = lang_spec.strip()
            if ';q=' in lang_spec:
                lang, quality = lang_spec.split(';q=', 1)
                try:
                    quality = float(quality)
                except ValueError:
                    quality = 1.0
            else:
                lang = lang_spec
                quality = 1.0
                
            # Extract primary language code
            primary_lang = lang.split('-')[0].lower()
            languages.append((primary_lang, quality))
            
        # Sort by quality and return highest
        languages.sort(key=lambda x: x[1], reverse=True)
        return languages[0][0] if languages else "en"


class AdaptiveRenderer:
    """
    Adaptive rendering engine that modifies responses based on client context.
    
    Automatically optimizes content delivery based on device capabilities,
    network conditions, and user preferences.
    """
    
    def __init__(self):
        self.image_sizes = {
            DeviceType.MOBILE: [(320, 240), (480, 360), (640, 480)],
            DeviceType.TABLET: [(768, 576), (1024, 768)],
            DeviceType.DESKTOP: [(1024, 768), (1440, 1080), (1920, 1440)]
        }
        
    def adapt_response(self, response_data: Dict[str, Any], 
                      context: RequestContext) -> Dict[str, Any]:
        """Adapt response based on client context"""
        
        if response_data.get("headers", {}).get("Content-Type") == "text/html":
            # Adapt HTML response
            body = response_data.get("body", "")
            adapted_body = self._adapt_html(body, context)
            
            response_data = response_data.copy()
            response_data["body"] = adapted_body
            
            # Add adaptive headers
            response_data["headers"] = {
                **response_data.get("headers", {}),
                **self._get_adaptive_headers(context)
            }
            
        return response_data
        
    def _adapt_html(self, html: str, context: RequestContext) -> str:
        """Adapt HTML content based on client context"""
        
        client = context.client_context
        
        # Image optimization
        if client.should_optimize_images():
            html = self._optimize_images(html, client)
            
        # CSS optimizations
        if client.prefers_dark_mode:
            html = self._inject_dark_mode_css(html)
            
        if client.should_reduce_animations():
            html = self._inject_reduced_motion_css(html)
            
        # JavaScript optimizations
        if client.is_low_end_device():
            html = self._optimize_javascript(html, client)
            
        # Font optimizations
        html = self._optimize_fonts(html, client)
        
        return html
        
    def _optimize_images(self, html: str, client: ClientContext) -> str:
        """Optimize images for client capabilities"""
        
        preferred_format = client.get_preferred_image_format()
        
        # Simple image replacement (in practice, this would be more sophisticated)
        if preferred_format == "webp":
            html = html.replace('.jpg"', '.webp"').replace('.png"', '.webp"')
        elif preferred_format == "avif":
            html = html.replace('.jpg"', '.avif"').replace('.png"', '.avif"')
            
        # Add responsive image attributes
        if client.is_mobile():
            # Add loading="lazy" and smaller sizes for mobile
            html = re.sub(
                r'<img ([^>]*src="[^"]+")([^>]*)>',
                r'<img \1 loading="lazy" sizes="(max-width: 480px) 480px, 100vw"\2>',
                html
            )
            
        return html
        
    def _inject_dark_mode_css(self, html: str) -> str:
        """Inject dark mode CSS"""
        
        dark_mode_css = """
        <style>
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #1a1a1a;
                --text-color: #ffffff;
                --border-color: #333333;
            }
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
            }
        }
        </style>
        """
        
        # Insert before closing head tag
        return html.replace('</head>', f'{dark_mode_css}</head>')
        
    def _inject_reduced_motion_css(self, html: str) -> str:
        """Inject reduced motion CSS"""
        
        reduced_motion_css = """
        <style>
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
        """
        
        return html.replace('</head>', f'{reduced_motion_css}</head>')
        
    def _optimize_javascript(self, html: str, client: ClientContext) -> str:
        """Optimize JavaScript for low-end devices"""
        
        # Add defer to script tags for better performance
        html = re.sub(r'<script ([^>]*src="[^"]+")([^>]*)>', r'<script defer \1\2>', html)
        
        # Add performance hints
        performance_script = """
        <script>
        // Reduce JavaScript execution on low-end devices
        if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 2) {
            window.PYFRAME_PERFORMANCE_MODE = 'low';
        }
        </script>
        """
        
        return html.replace('</head>', f'{performance_script}</head>')
        
    def _optimize_fonts(self, html: str, client: ClientContext) -> str:
        """Optimize font loading"""
        
        # Add font-display: swap for better performance
        html = re.sub(
            r'<link ([^>]*href="[^"]*fonts[^"]*")([^>]*)>',
            r'<link \1 font-display="swap"\2>',
            html
        )
        
        # Preload critical fonts on fast connections
        if client.connection_type == ConnectionType.FAST:
            font_preload = """
            <link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
            """
            html = html.replace('</head>', f'{font_preload}</head>')
            
        return html
        
    def _get_adaptive_headers(self, context: RequestContext) -> Dict[str, str]:
        """Get adaptive response headers"""
        
        headers = {}
        client = context.client_context
        
        # Vary header to indicate content varies by these factors
        vary_factors = ["User-Agent", "Accept", "Accept-Language"]
        
        if client.connection_type != ConnectionType.UNKNOWN:
            vary_factors.append("Save-Data")
            
        headers["Vary"] = ", ".join(vary_factors)
        
        # Cache control based on device type and connection
        if client.is_mobile() or client.connection_type in [ConnectionType.SLOW, ConnectionType.MODERATE]:
            # Longer cache for mobile/slow connections
            headers["Cache-Control"] = "public, max-age=86400"
        else:
            headers["Cache-Control"] = "public, max-age=3600"
            
        # Server timing headers for performance monitoring
        headers["Server-Timing"] = f"detect;dur=1, adapt;dur=2"
        
        return headers
