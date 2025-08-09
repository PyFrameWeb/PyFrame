"""
WebSocket Connection Management

Handles WebSocket connections for real-time bidirectional communication
between server and clients with automatic reconnection and state sync.
"""

import json
import uuid
import asyncio
import weakref
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types"""
    PING = "ping"
    PONG = "pong"
    DATA = "data"
    SYNC = "sync"
    ERROR = "error"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    STATE_UPDATE = "state_update"
    COMPONENT_UPDATE = "component_update"


@dataclass
class WebSocketMessage:
    """Structured WebSocket message"""
    type: MessageType
    data: Any = None
    channel: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "channel": self.channel,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id
        }
        
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            data=data.get("data"),
            channel=data.get("channel"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data["message_id"]
        )


class WebSocketConnection:
    """
    Represents a single WebSocket connection with state management.
    
    Handles message routing, subscriptions, and automatic reconnection.
    """
    
    def __init__(self, connection_id: str, websocket, client_info: Dict[str, Any] = None):
        self.connection_id = connection_id
        self.websocket = websocket
        self.client_info = client_info or {}
        
        self.state = ConnectionState.CONNECTING
        self.connected_at: Optional[datetime] = None
        self.last_ping: Optional[datetime] = None
        self.last_pong: Optional[datetime] = None
        
        # Subscriptions and state
        self.subscribed_channels: Set[str] = set()
        self.component_subscriptions: Set[str] = set()
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        
        # Message handling
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.send_queue: asyncio.Queue = asyncio.Queue()
        
        # Setup default handlers
        self._setup_default_handlers()
        
    def _setup_default_handlers(self):
        """Setup default message handlers"""
        self.add_message_handler(MessageType.PING, self._handle_ping)
        self.add_message_handler(MessageType.PONG, self._handle_pong)
        self.add_message_handler(MessageType.SUBSCRIBE, self._handle_subscribe)
        self.add_message_handler(MessageType.UNSUBSCRIBE, self._handle_unsubscribe)
        
    def add_message_handler(self, message_type: MessageType, handler: Callable):
        """Add a message handler for a specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        
    async def send_message(self, message: WebSocketMessage) -> None:
        """Send a message to the client"""
        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            print(f"Error sending message to {self.connection_id}: {e}")
            self.state = ConnectionState.ERROR
            
    async def send_data(self, data: Any, channel: str = None) -> None:
        """Send data message to client"""
        message = WebSocketMessage(
            type=MessageType.DATA,
            data=data,
            channel=channel
        )
        await self.send_message(message)
        
    async def send_state_update(self, component_id: str, state_data: Dict[str, Any]) -> None:
        """Send state update to client"""
        message = WebSocketMessage(
            type=MessageType.STATE_UPDATE,
            data={
                "component_id": component_id,
                "state": state_data
            }
        )
        await self.send_message(message)
        
    async def send_component_update(self, component_id: str, update_data: Dict[str, Any]) -> None:
        """Send component update to client"""
        message = WebSocketMessage(
            type=MessageType.COMPONENT_UPDATE,
            data={
                "component_id": component_id,
                "update": update_data
            }
        )
        await self.send_message(message)
        
    async def handle_message(self, raw_message: str) -> None:
        """Handle incoming message from client"""
        try:
            message = WebSocketMessage.from_json(raw_message)
            
            # Call registered handlers
            if message.type in self.message_handlers:
                for handler in self.message_handlers[message.type]:
                    await handler(message)
                    
        except Exception as e:
            print(f"Error handling message from {self.connection_id}: {e}")
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": str(e)}
            )
            await self.send_message(error_message)
            
    async def _handle_ping(self, message: WebSocketMessage) -> None:
        """Handle ping message"""
        self.last_ping = datetime.now()
        pong_message = WebSocketMessage(type=MessageType.PONG)
        await self.send_message(pong_message)
        
    async def _handle_pong(self, message: WebSocketMessage) -> None:
        """Handle pong message"""
        self.last_pong = datetime.now()
        
    async def _handle_subscribe(self, message: WebSocketMessage) -> None:
        """Handle channel subscription"""
        channel = message.data.get("channel")
        if channel:
            self.subscribed_channels.add(channel)
            
            # Notify channel manager
            from .channels import ChannelManager
            ChannelManager.subscribe_connection(channel, self)
            
    async def _handle_unsubscribe(self, message: WebSocketMessage) -> None:
        """Handle channel unsubscription"""
        channel = message.data.get("channel")
        if channel and channel in self.subscribed_channels:
            self.subscribed_channels.remove(channel)
            
            # Notify channel manager
            from .channels import ChannelManager
            ChannelManager.unsubscribe_connection(channel, self)
            
    def is_alive(self) -> bool:
        """Check if connection is alive"""
        if self.state != ConnectionState.CONNECTED:
            return False
            
        # Check if we've received a pong recently
        if self.last_ping and self.last_pong:
            ping_pong_diff = (self.last_ping - self.last_pong).total_seconds()
            return ping_pong_diff < 30  # 30 second timeout
            
        return True
        
    async def close(self) -> None:
        """Close the connection"""
        self.state = ConnectionState.DISCONNECTING
        
        # Unsubscribe from all channels
        for channel in list(self.subscribed_channels):
            from .channels import ChannelManager
            ChannelManager.unsubscribe_connection(channel, self)
            
        # Close websocket
        try:
            await self.websocket.close()
        except:
            pass
            
        self.state = ConnectionState.DISCONNECTED


class WebSocketManager:
    """
    Manages all WebSocket connections and provides broadcasting capabilities.
    
    Handles connection lifecycle, message routing, and real-time synchronization.
    """
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.heartbeat_interval = 30  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def add_connection(self, websocket, client_info: Dict[str, Any] = None) -> WebSocketConnection:
        """Add a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(connection_id, websocket, client_info)
        
        self.connections[connection_id] = connection
        connection.state = ConnectionState.CONNECTED
        connection.connected_at = datetime.now()
        
        # Associate with user if authenticated
        user_id = client_info.get("user_id") if client_info else None
        if user_id:
            connection.user_id = user_id
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
        # Start heartbeat if this is the first connection
        if len(self.connections) == 1 and not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
        print(f"WebSocket connection established: {connection_id}")
        return connection
        
    async def remove_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            # Remove from user connections
            if connection.user_id and connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
                    
            # Close connection
            await connection.close()
            del self.connections[connection_id]
            
            print(f"WebSocket connection removed: {connection_id}")
            
            # Stop heartbeat if no connections remain
            if not self.connections and self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None
                
    async def handle_connection(self, websocket, path: str = None) -> None:
        """Handle a new WebSocket connection"""
        connection = await self.add_connection(websocket)
        
        try:
            async for raw_message in websocket:
                await connection.handle_message(raw_message)
        except Exception as e:
            print(f"WebSocket error for {connection.connection_id}: {e}")
        finally:
            await self.remove_connection(connection.connection_id)
            
    async def broadcast_to_all(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
            
        # Send to all connections
        tasks = []
        for connection in self.connections.values():
            if connection.state == ConnectionState.CONNECTED:
                tasks.append(connection.send_message(message))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def broadcast_to_channel(self, channel: str, message: WebSocketMessage) -> None:
        """Broadcast message to all connections subscribed to a channel"""
        tasks = []
        
        for connection in self.connections.values():
            if (connection.state == ConnectionState.CONNECTED and 
                channel in connection.subscribed_channels):
                tasks.append(connection.send_message(message))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage) -> None:
        """Broadcast message to all connections for a specific user"""
        if user_id not in self.user_connections:
            return
            
        tasks = []
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.state == ConnectionState.CONNECTED:
                    tasks.append(connection.send_message(message))
                    
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def send_state_update(self, component_id: str, state_data: Dict[str, Any], 
                              channel: str = None, user_id: str = None) -> None:
        """Send state update to relevant connections"""
        message = WebSocketMessage(
            type=MessageType.STATE_UPDATE,
            data={
                "component_id": component_id,
                "state": state_data
            },
            channel=channel
        )
        
        if user_id:
            await self.broadcast_to_user(user_id, message)
        elif channel:
            await self.broadcast_to_channel(channel, message)
        else:
            await self.broadcast_to_all(message)
            
    async def send_component_update(self, component_id: str, update_data: Dict[str, Any],
                                  channel: str = None, user_id: str = None) -> None:
        """Send component update to relevant connections"""
        message = WebSocketMessage(
            type=MessageType.COMPONENT_UPDATE,
            data={
                "component_id": component_id,
                "update": update_data
            },
            channel=channel
        )
        
        if user_id:
            await self.broadcast_to_user(user_id, message)
        elif channel:
            await self.broadcast_to_channel(channel, message)
        else:
            await self.broadcast_to_all(message)
            
    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat to check connection health"""
        while self.connections:
            try:
                # Send ping to all connections
                ping_message = WebSocketMessage(type=MessageType.PING)
                await self.broadcast_to_all(ping_message)
                
                # Remove dead connections
                dead_connections = []
                for connection_id, connection in self.connections.items():
                    if not connection.is_alive():
                        dead_connections.append(connection_id)
                        
                for connection_id in dead_connections:
                    await self.remove_connection(connection_id)
                    
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.connections)
        active_connections = sum(1 for conn in self.connections.values() 
                               if conn.state == ConnectionState.CONNECTED)
        unique_users = len(self.user_connections)
        
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "unique_users": unique_users,
            "average_connections_per_user": active_connections / max(unique_users, 1)
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
