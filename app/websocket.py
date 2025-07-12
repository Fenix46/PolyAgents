"""
WebSocket connection manager for real-time communication.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

from .memory.redis_bus import RedisBus

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self, redis_bus: RedisBus):
        self.redis_bus = redis_bus
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.redis_subscription_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize the WebSocket manager."""
        logger.info("Initializing WebSocket connection manager")
        # Start listening for Redis messages
        self.redis_subscription_task = asyncio.create_task(self._listen_to_redis())
    
    async def cleanup(self) -> None:
        """Clean up WebSocket connections."""
        logger.info("Cleaning up WebSocket connections")
        
        # Cancel Redis subscription task
        if self.redis_subscription_task:
            self.redis_subscription_task.cancel()
            try:
                await self.redis_subscription_task
            except asyncio.CancelledError:
                pass
        
        # Close all active connections
        for conversation_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
        
        self.active_connections.clear()
    
    async def connect(self, websocket: WebSocket, conversation_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
        
        self.active_connections[conversation_id].add(websocket)
        logger.info(f"WebSocket connected for conversation {conversation_id}")
    
    async def disconnect(self, websocket: WebSocket, conversation_id: str) -> None:
        """Remove a WebSocket connection."""
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)
            
            # Remove conversation if no more connections
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        logger.info(f"WebSocket disconnected from conversation {conversation_id}")
    
    async def send_to_conversation(self, conversation_id: str, message: dict) -> None:
        """Send a message to all WebSocket connections for a conversation."""
        if conversation_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected_websockets = set()
        
        for websocket in self.active_connections[conversation_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error sending message to WebSocket: {e}")
                disconnected_websockets.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected_websockets:
            await self.disconnect(websocket, conversation_id)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send a message to a specific WebSocket connection."""
        try:
            message_json = json.dumps(message)
            await websocket.send_text(message_json)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def _listen_to_redis(self) -> None:
        """Listen for messages from Redis and broadcast to WebSocket connections."""
        try:
            async for message in self.redis_bus.subscribe_to_messages():
                # Parse the message to determine the conversation
                try:
                    if isinstance(message, dict) and 'conversation_id' in message:
                        conversation_id = message['conversation_id']
                        await self.send_to_conversation(conversation_id, message)
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info("Redis subscription task cancelled")
        except Exception as e:
            logger.error(f"Error in Redis subscription: {e}")
    
    def get_connection_count(self, conversation_id: str) -> int:
        """Get the number of active connections for a conversation."""
        return len(self.active_connections.get(conversation_id, set()))
    
    def get_total_connections(self) -> int:
        """Get the total number of active WebSocket connections."""
        return sum(len(connections) for connections in self.active_connections.values()) 