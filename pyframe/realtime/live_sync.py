"""
Live Synchronization Manager

Provides automatic state synchronization between backend and clients
with optimistic updates, conflict resolution, and offline support.
"""

import json
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.component import Component, State
from .websocket_manager import websocket_manager, WebSocketMessage, MessageType
from .sse_manager import sse_manager, SSEEvent, SSEEventType


class SyncEventType(Enum):
    """Types of synchronization events"""
    STATE_CHANGE = "state_change"
    COMPONENT_UPDATE = "component_update"
    MODEL_CREATE = "model_create"
    MODEL_UPDATE = "model_update"
    MODEL_DELETE = "model_delete"
    CUSTOM = "custom"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class SyncEvent:
    """Represents a synchronization event"""
    event_type: SyncEventType
    target_id: str  # Component ID, model ID, etc.
    data: Any
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    channel: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "target_id": self.target_id,
            "data": self.data,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "channel": self.channel,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "version": self.version
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncEvent':
        return cls(
            event_type=SyncEventType(data["event_type"]),
            target_id=data["target_id"],
            data=data["data"],
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            channel=data.get("channel"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_id=data["event_id"],
            version=data.get("version", 1)
        )


class SyncState:
    """Tracks synchronization state for components and models"""
    
    def __init__(self, target_id: str):
        self.target_id = target_id
        self.server_version = 0
        self.client_versions: Dict[str, int] = {}  # session_id -> version
        self.pending_changes: List[SyncEvent] = []
        self.last_sync: Optional[datetime] = None
        
    def increment_version(self, session_id: str = None) -> int:
        """Increment version for a session"""
        if session_id:
            current = self.client_versions.get(session_id, 0)
            self.client_versions[session_id] = current + 1
            return self.client_versions[session_id]
        else:
            self.server_version += 1
            return self.server_version
            
    def get_version(self, session_id: str = None) -> int:
        """Get current version for a session"""
        if session_id:
            return self.client_versions.get(session_id, 0)
        else:
            return self.server_version
            
    def has_conflicts(self, session_id: str) -> bool:
        """Check if there are version conflicts"""
        client_version = self.client_versions.get(session_id, 0)
        return client_version != self.server_version


class LiveSyncManager:
    """
    Manages live synchronization of state between server and clients.
    
    Provides optimistic updates, conflict resolution, and offline support.
    """
    
    def __init__(self):
        self.sync_states: Dict[str, SyncState] = {}
        self.component_subscribers: Dict[str, Set[str]] = {}  # component_id -> session_ids
        self.model_subscribers: Dict[str, Set[str]] = {}  # model_type -> session_ids
        self.conflict_resolution = ConflictResolution.SERVER_WINS
        
        # Event handlers
        self.event_handlers: Dict[SyncEventType, List[Callable]] = {}
        self.setup_default_handlers()
        
    def setup_default_handlers(self):
        """Setup default event handlers"""
        self.add_event_handler(SyncEventType.STATE_CHANGE, self._handle_state_change)
        self.add_event_handler(SyncEventType.COMPONENT_UPDATE, self._handle_component_update)
        self.add_event_handler(SyncEventType.MODEL_CREATE, self._handle_model_create)
        self.add_event_handler(SyncEventType.MODEL_UPDATE, self._handle_model_update)
        self.add_event_handler(SyncEventType.MODEL_DELETE, self._handle_model_delete)
        
    def add_event_handler(self, event_type: SyncEventType, handler: Callable):
        """Add an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def get_sync_state(self, target_id: str) -> SyncState:
        """Get or create sync state for a target"""
        if target_id not in self.sync_states:
            self.sync_states[target_id] = SyncState(target_id)
        return self.sync_states[target_id]
        
    async def sync_component_state(self, component_id: str, state_data: Dict[str, Any],
                                 session_id: str = None, user_id: str = None,
                                 channel: str = None) -> None:
        """Synchronize component state change"""
        
        sync_event = SyncEvent(
            event_type=SyncEventType.STATE_CHANGE,
            target_id=component_id,
            data=state_data,
            session_id=session_id,
            user_id=user_id,
            channel=channel
        )
        
        await self.process_sync_event(sync_event)
        
    async def sync_component_update(self, component_id: str, update_data: Dict[str, Any],
                                  session_id: str = None, user_id: str = None,
                                  channel: str = None) -> None:
        """Synchronize component update"""
        
        sync_event = SyncEvent(
            event_type=SyncEventType.COMPONENT_UPDATE,
            target_id=component_id,
            data=update_data,
            session_id=session_id,
            user_id=user_id,
            channel=channel
        )
        
        await self.process_sync_event(sync_event)
        
    async def sync_model_change(self, model_instance, operation: str,
                              session_id: str = None, user_id: str = None,
                              channel: str = None) -> None:
        """Synchronize model changes (create/update/delete)"""
        
        model_type = model_instance.__class__.__name__
        model_id = str(getattr(model_instance, 'id', 'unknown'))
        
        event_type_map = {
            'create': SyncEventType.MODEL_CREATE,
            'update': SyncEventType.MODEL_UPDATE,
            'delete': SyncEventType.MODEL_DELETE
        }
        
        sync_event = SyncEvent(
            event_type=event_type_map.get(operation, SyncEventType.MODEL_UPDATE),
            target_id=f"{model_type}:{model_id}",
            data={
                "model_type": model_type,
                "model_id": model_id,
                "model_data": model_instance.to_dict() if operation != 'delete' else None,
                "operation": operation
            },
            session_id=session_id,
            user_id=user_id,
            channel=channel
        )
        
        await self.process_sync_event(sync_event)
        
    async def process_sync_event(self, sync_event: SyncEvent) -> None:
        """Process a synchronization event"""
        
        # Get sync state
        sync_state = self.get_sync_state(sync_event.target_id)
        
        # Check for conflicts
        if sync_event.session_id and sync_state.has_conflicts(sync_event.session_id):
            await self._handle_conflict(sync_event, sync_state)
        else:
            # No conflicts, apply the change
            await self._apply_sync_event(sync_event, sync_state)
            
        # Update sync state
        sync_state.increment_version(sync_event.session_id)
        sync_state.last_sync = datetime.now()
        
    async def _apply_sync_event(self, sync_event: SyncEvent, sync_state: SyncState) -> None:
        """Apply a sync event"""
        
        # Call event handlers
        if sync_event.event_type in self.event_handlers:
            for handler in self.event_handlers[sync_event.event_type]:
                await handler(sync_event)
                
        # Broadcast to connected clients
        await self._broadcast_sync_event(sync_event)
        
    async def _handle_conflict(self, sync_event: SyncEvent, sync_state: SyncState) -> None:
        """Handle synchronization conflicts"""
        
        if self.conflict_resolution == ConflictResolution.SERVER_WINS:
            # Server version wins, reject client change
            await self._send_conflict_resolution(sync_event, "server_wins")
            
        elif self.conflict_resolution == ConflictResolution.CLIENT_WINS:
            # Client version wins, apply change
            await self._apply_sync_event(sync_event, sync_state)
            
        elif self.conflict_resolution == ConflictResolution.MERGE:
            # Attempt to merge changes
            merged_event = await self._merge_changes(sync_event, sync_state)
            if merged_event:
                await self._apply_sync_event(merged_event, sync_state)
            else:
                await self._send_conflict_resolution(sync_event, "merge_failed")
                
        else:  # MANUAL
            # Store for manual resolution
            sync_state.pending_changes.append(sync_event)
            await self._send_conflict_resolution(sync_event, "manual_required")
            
    async def _merge_changes(self, sync_event: SyncEvent, sync_state: SyncState) -> Optional[SyncEvent]:
        """Attempt to automatically merge conflicting changes"""
        
        # This is a simplified merge strategy
        # In practice, you'd implement more sophisticated merging
        
        if sync_event.event_type == SyncEventType.STATE_CHANGE:
            # For state changes, merge non-conflicting fields
            # This would need to compare with the current server state
            return sync_event  # Simplified: just accept the change
            
        # For other types, use manual resolution
        return None
        
    async def _send_conflict_resolution(self, sync_event: SyncEvent, resolution: str) -> None:
        """Send conflict resolution notification to client"""
        
        resolution_data = {
            "original_event": sync_event.to_dict(),
            "resolution": resolution,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send via WebSocket if available
        if sync_event.session_id:
            ws_message = WebSocketMessage(
                type=MessageType.SYNC,
                data={
                    "type": "conflict_resolution",
                    "resolution_data": resolution_data
                }
            )
            # Would need to map session_id to connection_id
            # await websocket_manager.send_to_session(sync_event.session_id, ws_message)
            
        # Send via SSE
        if sync_event.user_id:
            await sse_manager.send_data_to_user(
                sync_event.user_id,
                {
                    "type": "conflict_resolution",
                    "resolution_data": resolution_data
                },
                SSEEventType.SYNC
            )
            
    async def _broadcast_sync_event(self, sync_event: SyncEvent) -> None:
        """Broadcast sync event to relevant clients"""
        
        event_data = sync_event.to_dict()
        
        # Broadcast via WebSocket
        ws_message = WebSocketMessage(
            type=MessageType.SYNC,
            data=event_data,
            channel=sync_event.channel
        )
        
        if sync_event.user_id:
            await websocket_manager.broadcast_to_user(sync_event.user_id, ws_message)
        elif sync_event.channel:
            await websocket_manager.broadcast_to_channel(sync_event.channel, ws_message)
        else:
            await websocket_manager.broadcast_to_all(ws_message)
            
        # Broadcast via SSE
        sse_event = SSEEvent(
            event_type=SSEEventType.SYNC,
            data=event_data
        )
        
        if sync_event.user_id:
            await sse_manager.broadcast_to_user(sync_event.user_id, sse_event)
        elif sync_event.channel:
            await sse_manager.broadcast_to_channel(sync_event.channel, sse_event)
        else:
            await sse_manager.broadcast_to_all(sse_event)
            
    async def _handle_state_change(self, sync_event: SyncEvent) -> None:
        """Handle component state change event"""
        
        component_id = sync_event.target_id
        state_data = sync_event.data
        
        # Update component state on server if needed
        # This would integrate with the component system
        
        print(f"State change for component {component_id}: {state_data}")
        
    async def _handle_component_update(self, sync_event: SyncEvent) -> None:
        """Handle component update event"""
        
        component_id = sync_event.target_id
        update_data = sync_event.data
        
        print(f"Component update for {component_id}: {update_data}")
        
    async def _handle_model_create(self, sync_event: SyncEvent) -> None:
        """Handle model creation event"""
        
        model_data = sync_event.data
        model_type = model_data.get("model_type")
        
        print(f"Model created: {model_type}")
        
    async def _handle_model_update(self, sync_event: SyncEvent) -> None:
        """Handle model update event"""
        
        model_data = sync_event.data
        model_type = model_data.get("model_type")
        model_id = model_data.get("model_id")
        
        print(f"Model updated: {model_type}:{model_id}")
        
    async def _handle_model_delete(self, sync_event: SyncEvent) -> None:
        """Handle model deletion event"""
        
        model_data = sync_event.data
        model_type = model_data.get("model_type")
        model_id = model_data.get("model_id")
        
        print(f"Model deleted: {model_type}:{model_id}")
        
    def subscribe_to_component(self, component_id: str, session_id: str) -> None:
        """Subscribe a session to component updates"""
        if component_id not in self.component_subscribers:
            self.component_subscribers[component_id] = set()
        self.component_subscribers[component_id].add(session_id)
        
    def unsubscribe_from_component(self, component_id: str, session_id: str) -> None:
        """Unsubscribe a session from component updates"""
        if component_id in self.component_subscribers:
            self.component_subscribers[component_id].discard(session_id)
            if not self.component_subscribers[component_id]:
                del self.component_subscribers[component_id]
                
    def subscribe_to_model(self, model_type: str, session_id: str) -> None:
        """Subscribe a session to model updates"""
        if model_type not in self.model_subscribers:
            self.model_subscribers[model_type] = set()
        self.model_subscribers[model_type].add(session_id)
        
    def unsubscribe_from_model(self, model_type: str, session_id: str) -> None:
        """Unsubscribe a session from model updates"""
        if model_type in self.model_subscribers:
            self.model_subscribers[model_type].discard(session_id)
            if not self.model_subscribers[model_type]:
                del self.model_subscribers[model_type]
                
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        
        total_sync_states = len(self.sync_states)
        component_subscriptions = sum(len(subs) for subs in self.component_subscribers.values())
        model_subscriptions = sum(len(subs) for subs in self.model_subscribers.values())
        
        conflicts = sum(1 for state in self.sync_states.values() if state.pending_changes)
        
        return {
            "total_sync_states": total_sync_states,
            "component_subscriptions": component_subscriptions,
            "model_subscriptions": model_subscriptions,
            "pending_conflicts": conflicts
        }


# Global live sync manager instance
live_sync_manager = LiveSyncManager()
