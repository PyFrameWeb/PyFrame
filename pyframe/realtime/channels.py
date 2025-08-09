"""
Channel Management System

Provides organized broadcasting channels for real-time communication
with subscription management and access control.
"""

import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ChannelType(Enum):
    """Types of communication channels"""
    PUBLIC = "public"           # Anyone can subscribe
    PRIVATE = "private"         # Invite-only
    USER_SPECIFIC = "user"      # User-specific channel
    BROADCAST = "broadcast"     # One-way broadcasting
    PRESENCE = "presence"       # Shows online users


@dataclass
class ChannelMember:
    """Represents a member of a channel"""
    connection_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    joined_at: datetime = field(default_factory=datetime.now)
    permissions: Set[str] = field(default_factory=set)
    
    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission"""
        return permission in self.permissions or "admin" in self.permissions


class Channel:
    """
    Represents a communication channel for real-time updates.
    
    Channels organize related real-time communications and provide
    access control and permission management.
    """
    
    def __init__(self, channel_id: str, channel_type: ChannelType = ChannelType.PUBLIC,
                 name: str = None, description: str = None, 
                 creator_id: str = None):
        self.channel_id = channel_id
        self.channel_type = channel_type
        self.name = name or channel_id
        self.description = description
        self.creator_id = creator_id
        self.created_at = datetime.now()
        
        # Member management
        self.members: Dict[str, ChannelMember] = {}
        self.max_members: Optional[int] = None
        
        # Message history
        self.message_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Channel settings
        self.is_active = True
        self.allow_history = True
        self.require_invitation = channel_type == ChannelType.PRIVATE
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
    def add_member(self, connection_id: str, user_id: str = None, 
                  session_id: str = None, permissions: Set[str] = None) -> bool:
        """Add a member to the channel"""
        
        # Check if channel is full
        if self.max_members and len(self.members) >= self.max_members:
            return False
            
        # Check if invitation is required
        if self.require_invitation and not self._has_invitation(connection_id):
            return False
            
        # Add member
        member = ChannelMember(
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            permissions=permissions or set()
        )
        
        self.members[connection_id] = member
        
        # Trigger join event
        self._trigger_event("member_joined", {
            "connection_id": connection_id,
            "user_id": user_id,
            "member_count": len(self.members)
        })
        
        return True
        
    def remove_member(self, connection_id: str) -> bool:
        """Remove a member from the channel"""
        
        if connection_id in self.members:
            member = self.members.pop(connection_id)
            
            # Trigger leave event
            self._trigger_event("member_left", {
                "connection_id": connection_id,
                "user_id": member.user_id,
                "member_count": len(self.members)
            })
            
            return True
            
        return False
        
    def get_member(self, connection_id: str) -> Optional[ChannelMember]:
        """Get member by connection ID"""
        return self.members.get(connection_id)
        
    def get_members_by_user(self, user_id: str) -> List[ChannelMember]:
        """Get all members for a specific user"""
        return [member for member in self.members.values() 
                if member.user_id == user_id]
        
    def has_member(self, connection_id: str) -> bool:
        """Check if connection is a member"""
        return connection_id in self.members
        
    def can_send_message(self, connection_id: str) -> bool:
        """Check if member can send messages"""
        member = self.get_member(connection_id)
        if not member:
            return False
            
        if self.channel_type == ChannelType.BROADCAST:
            return member.has_permission("broadcast")
            
        return True
        
    def add_message_to_history(self, message: Dict[str, Any]) -> None:
        """Add message to channel history"""
        
        if not self.allow_history:
            return
            
        message_entry = {
            **message,
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        self.message_history.append(message_entry)
        
        # Trim history if needed
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
            
    def get_recent_messages(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from history"""
        return self.message_history[-count:] if self.message_history else []
        
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def _trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger channel event"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(self, event_type, data)
                except Exception as e:
                    print(f"Error in channel event handler: {e}")
                    
    def _has_invitation(self, connection_id: str) -> bool:
        """Check if connection has invitation (placeholder)"""
        # In a real implementation, this would check an invitations system
        return True
        
    def get_stats(self) -> Dict[str, Any]:
        """Get channel statistics"""
        user_ids = {member.user_id for member in self.members.values() if member.user_id}
        
        return {
            "channel_id": self.channel_id,
            "channel_type": self.channel_type.value,
            "member_count": len(self.members),
            "unique_users": len(user_ids),
            "message_count": len(self.message_history),
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary"""
        return {
            "channel_id": self.channel_id,
            "channel_type": self.channel_type.value,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat(),
            "member_count": len(self.members),
            "is_active": self.is_active,
            "allow_history": self.allow_history,
            "require_invitation": self.require_invitation
        }


class ChannelManager:
    """
    Manages all communication channels and their memberships.
    
    Provides channel creation, subscription management, and
    broadcasting capabilities across the application.
    """
    
    def __init__(self):
        self.channels: Dict[str, Channel] = {}
        self.connection_channels: Dict[str, Set[str]] = {}  # connection_id -> channel_ids
        self.user_channels: Dict[str, Set[str]] = {}  # user_id -> channel_ids
        
        # Create default channels
        self._create_default_channels()
        
    def _create_default_channels(self) -> None:
        """Create default system channels"""
        
        # Global broadcast channel
        self.create_channel(
            "global",
            ChannelType.BROADCAST,
            name="Global Broadcast",
            description="System-wide announcements"
        )
        
        # General public channel
        self.create_channel(
            "general",
            ChannelType.PUBLIC,
            name="General",
            description="General discussion"
        )
        
    def create_channel(self, channel_id: str, channel_type: ChannelType = ChannelType.PUBLIC,
                      name: str = None, description: str = None,
                      creator_id: str = None) -> Channel:
        """Create a new channel"""
        
        if channel_id in self.channels:
            raise ValueError(f"Channel {channel_id} already exists")
            
        channel = Channel(
            channel_id=channel_id,
            channel_type=channel_type,
            name=name,
            description=description,
            creator_id=creator_id
        )
        
        self.channels[channel_id] = channel
        
        print(f"Channel created: {channel_id} ({channel_type.value})")
        return channel
        
    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel"""
        
        if channel_id not in self.channels:
            return False
            
        channel = self.channels[channel_id]
        
        # Remove all members
        for connection_id in list(channel.members.keys()):
            self.unsubscribe_connection(channel_id, connection_id)
            
        # Remove channel
        del self.channels[channel_id]
        
        print(f"Channel deleted: {channel_id}")
        return True
        
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get channel by ID"""
        return self.channels.get(channel_id)
        
    def subscribe_connection(self, channel_id: str, connection_id: str,
                           user_id: str = None, session_id: str = None,
                           permissions: Set[str] = None) -> bool:
        """Subscribe a connection to a channel"""
        
        channel = self.get_channel(channel_id)
        if not channel:
            return False
            
        # Add to channel
        if not channel.add_member(connection_id, user_id, session_id, permissions):
            return False
            
        # Update tracking
        if connection_id not in self.connection_channels:
            self.connection_channels[connection_id] = set()
        self.connection_channels[connection_id].add(channel_id)
        
        if user_id:
            if user_id not in self.user_channels:
                self.user_channels[user_id] = set()
            self.user_channels[user_id].add(channel_id)
            
        return True
        
    def unsubscribe_connection(self, channel_id: str, connection_id: str) -> bool:
        """Unsubscribe a connection from a channel"""
        
        channel = self.get_channel(channel_id)
        if not channel:
            return False
            
        # Get member info before removal
        member = channel.get_member(connection_id)
        user_id = member.user_id if member else None
        
        # Remove from channel
        if not channel.remove_member(connection_id):
            return False
            
        # Update tracking
        if connection_id in self.connection_channels:
            self.connection_channels[connection_id].discard(channel_id)
            if not self.connection_channels[connection_id]:
                del self.connection_channels[connection_id]
                
        if user_id and user_id in self.user_channels:
            # Check if user has other connections in this channel
            user_members = channel.get_members_by_user(user_id)
            if not user_members:
                self.user_channels[user_id].discard(channel_id)
                if not self.user_channels[user_id]:
                    del self.user_channels[user_id]
                    
        return True
        
    def get_connection_channels(self, connection_id: str) -> List[str]:
        """Get all channels for a connection"""
        return list(self.connection_channels.get(connection_id, set()))
        
    def get_user_channels(self, user_id: str) -> List[str]:
        """Get all channels for a user"""
        return list(self.user_channels.get(user_id, set()))
        
    def get_channel_members(self, channel_id: str) -> List[ChannelMember]:
        """Get all members of a channel"""
        channel = self.get_channel(channel_id)
        return list(channel.members.values()) if channel else []
        
    def broadcast_to_channel(self, channel_id: str, message: Dict[str, Any],
                           sender_connection_id: str = None) -> List[str]:
        """Broadcast message to channel members"""
        
        channel = self.get_channel(channel_id)
        if not channel:
            return []
            
        # Check sender permissions
        if sender_connection_id and not channel.can_send_message(sender_connection_id):
            return []
            
        # Add to history
        channel.add_message_to_history(message)
        
        # Get recipient connection IDs
        recipients = []
        for connection_id in channel.members:
            if connection_id != sender_connection_id:  # Don't echo back to sender
                recipients.append(connection_id)
                
        return recipients
        
    def create_user_channel(self, user_id: str) -> str:
        """Create a private channel for a user"""
        channel_id = f"user:{user_id}"
        
        if channel_id not in self.channels:
            self.create_channel(
                channel_id,
                ChannelType.USER_SPECIFIC,
                name=f"User {user_id}",
                description=f"Private channel for user {user_id}"
            )
            
        return channel_id
        
    def create_presence_channel(self, resource_id: str) -> str:
        """Create a presence channel for a resource"""
        channel_id = f"presence:{resource_id}"
        
        if channel_id not in self.channels:
            channel = self.create_channel(
                channel_id,
                ChannelType.PRESENCE,
                name=f"Presence {resource_id}",
                description=f"Presence tracking for {resource_id}"
            )
            
            # Add presence tracking handlers
            channel.add_event_handler("member_joined", self._handle_presence_join)
            channel.add_event_handler("member_left", self._handle_presence_leave)
            
        return channel_id
        
    def _handle_presence_join(self, channel: Channel, event_type: str, data: Dict[str, Any]) -> None:
        """Handle presence join event"""
        presence_message = {
            "type": "presence",
            "action": "join",
            "user_id": data.get("user_id"),
            "connection_id": data["connection_id"],
            "member_count": data["member_count"]
        }
        
        # Broadcast presence update (would integrate with real-time managers)
        print(f"Presence join in {channel.channel_id}: {presence_message}")
        
    def _handle_presence_leave(self, channel: Channel, event_type: str, data: Dict[str, Any]) -> None:
        """Handle presence leave event"""
        presence_message = {
            "type": "presence",
            "action": "leave",
            "user_id": data.get("user_id"),
            "connection_id": data["connection_id"],
            "member_count": data["member_count"]
        }
        
        # Broadcast presence update (would integrate with real-time managers)
        print(f"Presence leave in {channel.channel_id}: {presence_message}")
        
    def get_public_channels(self) -> List[Dict[str, Any]]:
        """Get list of public channels"""
        public_channels = []
        
        for channel in self.channels.values():
            if channel.channel_type == ChannelType.PUBLIC and channel.is_active:
                public_channels.append(channel.to_dict())
                
        return public_channels
        
    def get_stats(self) -> Dict[str, Any]:
        """Get channel manager statistics"""
        
        total_channels = len(self.channels)
        active_channels = sum(1 for ch in self.channels.values() if ch.is_active)
        total_members = sum(len(ch.members) for ch in self.channels.values())
        
        channel_types = {}
        for channel in self.channels.values():
            channel_type = channel.channel_type.value
            channel_types[channel_type] = channel_types.get(channel_type, 0) + 1
            
        return {
            "total_channels": total_channels,
            "active_channels": active_channels,
            "total_members": total_members,
            "channel_types": channel_types,
            "average_members_per_channel": total_members / max(total_channels, 1)
        }


# Global channel manager instance
channel_manager = ChannelManager()
