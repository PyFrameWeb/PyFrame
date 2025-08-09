"""
Server-Sent Events (SSE) Manager

Provides one-way real-time communication from server to clients
using Server-Sent Events with automatic reconnection and streaming.
"""

import json
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Callable, Set, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SSEEventType(Enum):
    """SSE event types"""
    MESSAGE = "message"
    DATA = "data"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    STATE_UPDATE = "state_update"
    COMPONENT_UPDATE = "component_update"
    SYNC = "sync"


@dataclass
class SSEEvent:
    """Server-Sent Event structure"""
    event_type: SSEEventType
    data: Any = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    retry: Optional[int] = None  # Retry timeout in milliseconds
    
    def format(self) -> str:
        """Format event for SSE transmission"""
        lines = []
        
        # Event ID
        lines.append(f"id: {self.event_id}")
        
        # Event type
        lines.append(f"event: {self.event_type.value}")
        
        # Data (JSON encoded)
        if self.data is not None:
            data_json = json.dumps(self.data, default=str)
            # Split multiline data
            for line in data_json.split('\n'):
                lines.append(f"data: {line}")
        else:
            lines.append("data: ")
            
        # Retry timeout
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
            
        # End with double newline
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)


class SSEConnection:
    """
    Represents a single SSE connection.
    
    Manages event streaming and connection state for a client.
    """
    
    def __init__(self, connection_id: str, client_info: Dict[str, Any] = None):
        self.connection_id = connection_id
        self.client_info = client_info or {}
        
        self.connected_at = datetime.now()
        self.last_event_id: Optional[str] = None
        self.is_active = True
        
        # Subscriptions
        self.subscribed_channels: Set[str] = set()
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        
        # Event queue for this connection
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        # Extract user info
        if client_info:
            self.user_id = client_info.get("user_id")
            self.session_id = client_info.get("session_id")
            
    async def send_event(self, event: SSEEvent) -> None:
        """Queue an event for transmission"""
        if self.is_active:
            await self.event_queue.put(event)
            self.last_event_id = event.event_id
            
    async def send_data(self, data: Any, event_type: SSEEventType = SSEEventType.DATA) -> None:
        """Send data event"""
        event = SSEEvent(event_type=event_type, data=data)
        await self.send_event(event)
        
    async def send_heartbeat(self) -> None:
        """Send heartbeat event"""
        event = SSEEvent(
            event_type=SSEEventType.HEARTBEAT,
            data={"timestamp": datetime.now().isoformat()}
        )
        await self.send_event(event)
        
    async def send_state_update(self, component_id: str, state_data: Dict[str, Any]) -> None:
        """Send state update event"""
        event = SSEEvent(
            event_type=SSEEventType.STATE_UPDATE,
            data={
                "component_id": component_id,
                "state": state_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.send_event(event)
        
    async def send_component_update(self, component_id: str, update_data: Dict[str, Any]) -> None:
        """Send component update event"""
        event = SSEEvent(
            event_type=SSEEventType.COMPONENT_UPDATE,
            data={
                "component_id": component_id,
                "update": update_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.send_event(event)
        
    def subscribe_to_channel(self, channel: str) -> None:
        """Subscribe to a channel"""
        self.subscribed_channels.add(channel)
        
    def unsubscribe_from_channel(self, channel: str) -> None:
        """Unsubscribe from a channel"""
        self.subscribed_channels.discard(channel)
        
    async def close(self) -> None:
        """Close the connection"""
        self.is_active = False
        
        # Clear event queue
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
    async def event_stream(self) -> AsyncGenerator[str, None]:
        """Generate event stream for this connection"""
        
        # Send initial connection event
        initial_event = SSEEvent(
            event_type=SSEEventType.MESSAGE,
            data={
                "type": "connected",
                "connection_id": self.connection_id,
                "timestamp": self.connected_at.isoformat()
            }
        )
        yield initial_event.format()
        
        # Stream events from queue
        while self.is_active:
            try:
                # Wait for event with timeout for heartbeat
                event = await asyncio.wait_for(self.event_queue.get(), timeout=30.0)
                yield event.format()
                
            except asyncio.TimeoutError:
                # Send heartbeat on timeout
                await self.send_heartbeat()
                
            except Exception as e:
                # Send error and close
                error_event = SSEEvent(
                    event_type=SSEEventType.ERROR,
                    data={"error": str(e)}
                )
                yield error_event.format()
                break


class SSEManager:
    """
    Manages all SSE connections and provides broadcasting capabilities.
    
    Handles connection lifecycle and real-time event distribution.
    """
    
    def __init__(self):
        self.connections: Dict[str, SSEConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.channel_connections: Dict[str, Set[str]] = {}  # channel -> connection_ids
        
    def create_connection(self, client_info: Dict[str, Any] = None, 
                         last_event_id: str = None) -> SSEConnection:
        """Create a new SSE connection"""
        connection_id = str(uuid.uuid4())
        connection = SSEConnection(connection_id, client_info)
        
        if last_event_id:
            connection.last_event_id = last_event_id
            
        self.connections[connection_id] = connection
        
        # Associate with user
        if connection.user_id:
            if connection.user_id not in self.user_connections:
                self.user_connections[connection.user_id] = set()
            self.user_connections[connection.user_id].add(connection_id)
            
        print(f"SSE connection created: {connection_id}")
        return connection
        
    async def remove_connection(self, connection_id: str) -> None:
        """Remove an SSE connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            # Remove from user connections
            if connection.user_id and connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
                    
            # Remove from channel subscriptions
            for channel in list(connection.subscribed_channels):
                self.unsubscribe_from_channel(connection_id, channel)
                
            # Close connection
            await connection.close()
            del self.connections[connection_id]
            
            print(f"SSE connection removed: {connection_id}")
            
    def subscribe_to_channel(self, connection_id: str, channel: str) -> None:
        """Subscribe a connection to a channel"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.subscribe_to_channel(channel)
            
            if channel not in self.channel_connections:
                self.channel_connections[channel] = set()
            self.channel_connections[channel].add(connection_id)
            
    def unsubscribe_from_channel(self, connection_id: str, channel: str) -> None:
        """Unsubscribe a connection from a channel"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.unsubscribe_from_channel(channel)
            
            if channel in self.channel_connections:
                self.channel_connections[channel].discard(connection_id)
                if not self.channel_connections[channel]:
                    del self.channel_connections[channel]
                    
    async def broadcast_to_all(self, event: SSEEvent) -> None:
        """Broadcast event to all connections"""
        tasks = []
        for connection in self.connections.values():
            if connection.is_active:
                tasks.append(connection.send_event(event))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def broadcast_to_channel(self, channel: str, event: SSEEvent) -> None:
        """Broadcast event to all connections in a channel"""
        if channel not in self.channel_connections:
            return
            
        tasks = []
        for connection_id in self.channel_connections[channel]:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_active:
                    tasks.append(connection.send_event(event))
                    
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def broadcast_to_user(self, user_id: str, event: SSEEvent) -> None:
        """Broadcast event to all connections for a user"""
        if user_id not in self.user_connections:
            return
            
        tasks = []
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_active:
                    tasks.append(connection.send_event(event))
                    
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def send_data_to_all(self, data: Any, event_type: SSEEventType = SSEEventType.DATA) -> None:
        """Send data to all connections"""
        event = SSEEvent(event_type=event_type, data=data)
        await self.broadcast_to_all(event)
        
    async def send_data_to_channel(self, channel: str, data: Any, 
                                 event_type: SSEEventType = SSEEventType.DATA) -> None:
        """Send data to a specific channel"""
        event = SSEEvent(event_type=event_type, data=data)
        await self.broadcast_to_channel(channel, event)
        
    async def send_data_to_user(self, user_id: str, data: Any,
                              event_type: SSEEventType = SSEEventType.DATA) -> None:
        """Send data to a specific user"""
        event = SSEEvent(event_type=event_type, data=data)
        await self.broadcast_to_user(user_id, event)
        
    async def send_state_update(self, component_id: str, state_data: Dict[str, Any],
                              channel: str = None, user_id: str = None) -> None:
        """Send state update to relevant connections"""
        event = SSEEvent(
            event_type=SSEEventType.STATE_UPDATE,
            data={
                "component_id": component_id,
                "state": state_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if user_id:
            await self.broadcast_to_user(user_id, event)
        elif channel:
            await self.broadcast_to_channel(channel, event)
        else:
            await self.broadcast_to_all(event)
            
    async def send_component_update(self, component_id: str, update_data: Dict[str, Any],
                                  channel: str = None, user_id: str = None) -> None:
        """Send component update to relevant connections"""
        event = SSEEvent(
            event_type=SSEEventType.COMPONENT_UPDATE,
            data={
                "component_id": component_id,
                "update": update_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if user_id:
            await self.broadcast_to_user(user_id, event)
        elif channel:
            await self.broadcast_to_channel(channel, event)
        else:
            await self.broadcast_to_all(event)
            
    async def create_sse_response(self, connection_id: str) -> AsyncGenerator[str, None]:
        """Create SSE response generator for a connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            try:
                async for event_data in connection.event_stream():
                    yield event_data
                    
            except Exception as e:
                print(f"SSE stream error for {connection_id}: {e}")
            finally:
                await self.remove_connection(connection_id)
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.connections)
        active_connections = sum(1 for conn in self.connections.values() if conn.is_active)
        unique_users = len(self.user_connections)
        total_channels = len(self.channel_connections)
        
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "unique_users": unique_users,
            "total_channels": total_channels,
            "average_connections_per_user": active_connections / max(unique_users, 1)
        }


# Global SSE manager instance
sse_manager = SSEManager()
