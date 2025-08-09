"""
PyFrame Real-time Module

Provides reactive live updates between backend and clients using
WebSockets and Server-Sent Events with automatic synchronization.
"""

from .websocket_manager import WebSocketManager, WebSocketConnection
from .sse_manager import SSEManager, SSEConnection
from .live_sync import LiveSyncManager, SyncEvent
from .channels import Channel, ChannelManager

__all__ = [
    "WebSocketManager", 
    "WebSocketConnection",
    "SSEManager", 
    "SSEConnection",
    "LiveSyncManager", 
    "SyncEvent",
    "Channel",
    "ChannelManager"
]
