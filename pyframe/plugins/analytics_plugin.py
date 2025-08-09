"""
Analytics Plugin

Provides analytics and metrics collection for PyFrame applications
with privacy-focused tracking and customizable data collection.
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .plugin import Plugin, PluginInfo, HookType


@dataclass
class AnalyticsEvent:
    """Represents an analytics event"""
    event_type: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "properties": self.properties
        }


class AnalyticsPlugin(Plugin):
    """
    Analytics plugin for tracking user behavior and application metrics.
    
    Features:
    - Privacy-focused tracking
    - Custom event collection
    - Performance metrics
    - User journey tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.events: List[AnalyticsEvent] = []
        self.enabled = self.get_config("enabled", True)
        self.privacy_mode = self.get_config("privacy_mode", True)
        
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="analytics",
            version="1.0.0", 
            description="Privacy-focused analytics and metrics collection",
            author="PyFrame Team",
            tags=["analytics", "metrics", "tracking"]
        )
        
    async def initialize(self, app) -> None:
        """Initialize analytics plugin"""
        
        if not self.enabled:
            return
            
        # Register hooks
        self.register_hook(HookType.AFTER_REQUEST, self._track_request, priority=90)
        
        # Add analytics utilities to app
        app.analytics = self
        
        print("Analytics plugin initialized")
        
    def track_event(self, event_type: str, properties: Dict[str, Any] = None,
                   user_id: str = None, session_id: str = None) -> None:
        """Track a custom event"""
        
        if not self.enabled:
            return
            
        event = AnalyticsEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id if not self.privacy_mode else None,
            session_id=session_id,
            properties=properties or {}
        )
        
        self.events.append(event)
        
    async def _track_request(self, context: Dict[str, Any], *args, **kwargs) -> None:
        """Track request analytics"""
        
        request_context = kwargs.get("request_context")
        response = kwargs.get("response")
        
        if not request_context:
            return
            
        properties = {
            "method": request_context.method,
            "path": request_context.path,
            "status": response.get("status") if response else None,
            "user_agent": request_context.headers.get("user-agent"),
            "referer": request_context.headers.get("referer")
        }
        
        self.track_event(
            "page_view",
            properties,
            user_id=context.get("user_id"),
            session_id=context.get("session_id")
        )
