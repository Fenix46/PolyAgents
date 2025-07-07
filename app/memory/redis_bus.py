"""Redis bus for inter-agent communication using Redis Streams."""

import json
import logging
from typing import List, Optional, Dict, Any
import redis.asyncio as redis

from ..models import Message
from ..config import settings

logger = logging.getLogger(__name__)


class RedisBus:
    """Redis-based message bus using Redis Streams for agent communication."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("Connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Disconnected from Redis")
    
    async def send_message(self, channel: str, message: Message) -> str:
        """Send message to Redis stream."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            # Serialize message to Redis stream
            message_data = {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender": message.sender,
                "content": message.content,
                "turn": str(message.turn),
                "timestamp": message.timestamp.isoformat(),
                "metadata": json.dumps(message.metadata) if message.metadata else "{}"
            }
            
            # Add to stream
            stream_id = await self.redis_client.xadd(
                channel, 
                message_data,
                maxlen=settings.redis_stream_maxlen
            )
            
            logger.debug(f"Sent message {message.id} to stream {channel}: {stream_id}")
            return stream_id
            
        except Exception as e:
            logger.error(f"Error sending message to Redis: {e}")
            raise
    
    async def get_conversation_history(
        self, 
        channel: str, 
        count: int = 50
    ) -> List[Message]:
        """Get conversation history from Redis stream."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            # Read from stream (latest messages)
            stream_data = await self.redis_client.xrevrange(
                channel,
                count=count
            )
            
            messages = []
            for stream_id, fields in reversed(stream_data):  # Reverse to get chronological order
                try:
                    message = Message(
                        id=fields["id"],
                        conversation_id=fields["conversation_id"],
                        sender=fields["sender"],
                        content=fields["content"],
                        turn=int(fields["turn"]),
                        timestamp=fields["timestamp"],
                        metadata=json.loads(fields.get("metadata", "{}"))
                    )
                    messages.append(message)
                except Exception as e:
                    logger.warning(f"Failed to parse message from stream: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(messages)} messages from {channel}")
            return messages
            
        except Exception as e:
            logger.error(f"Error reading from Redis stream: {e}")
            return []
    
    async def subscribe_to_conversation(
        self, 
        channel: str, 
        consumer_group: str,
        consumer_name: str
    ) -> None:
        """
        Subscribe to conversation updates using Redis consumer groups.
        TODO: Implement for real-time message processing.
        """
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(
                    channel, 
                    consumer_group, 
                    id="0", 
                    mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
            
            # TODO: Implement message consumption loop
            raise NotImplementedError("Real-time subscription not yet implemented")
            
        except Exception as e:
            logger.error(f"Error subscribing to conversation: {e}")
            raise
    
    async def get_active_conversations(self) -> List[str]:
        """Get list of active conversation channels."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            # Find all chat:* streams
            chat_streams = await self.redis_client.keys("chat:*")
            return [stream for stream in chat_streams if await self.redis_client.exists(stream)]
            
        except Exception as e:
            logger.error(f"Error getting active conversations: {e}")
            return []
    
    async def cleanup_old_conversations(self, max_age_hours: int = 24) -> int:
        """
        Clean up old conversation streams.
        TODO: Implement based on timestamp.
        """
        # TODO: Implement cleanup logic based on stream age
        raise NotImplementedError("Conversation cleanup not yet implemented") 