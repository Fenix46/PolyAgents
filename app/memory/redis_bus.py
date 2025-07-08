"""Redis bus for inter-agent communication using Redis Streams."""

import json
import logging
import asyncio
from typing import List, Optional, Dict, Any, Callable, AsyncGenerator
import redis.asyncio as redis

from ..models import Message
from ..config import settings

logger = logging.getLogger(__name__)


class RedisBus:
    """Redis-based message bus using Redis Streams for agent communication."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False
        self._subscription_tasks: Dict[str, asyncio.Task] = {}
    
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
        # Cancel all subscription tasks
        for task in self._subscription_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._subscription_tasks:
            await asyncio.gather(*self._subscription_tasks.values(), return_exceptions=True)
        
        self._subscription_tasks.clear()
        
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
    
    async def create_consumer_group(
        self, 
        stream: str, 
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """Create a consumer group for a stream."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            await self.redis_client.xgroup_create(
                stream, 
                group_name, 
                id=start_id, 
                mkstream=True
            )
            logger.info(f"Created consumer group '{group_name}' for stream '{stream}'")
            return True
            
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{group_name}' already exists for stream '{stream}'")
                return True
            else:
                logger.error(f"Error creating consumer group: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating consumer group: {e}")
            raise
    
    async def subscribe_to_conversation(
        self, 
        channel: str, 
        consumer_group: str,
        consumer_name: str,
        message_handler: Callable[[Message], None]
    ) -> None:
        """
        Subscribe to conversation updates using Redis consumer groups.
        """
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            # Create consumer group if it doesn't exist
            await self.create_consumer_group(channel, consumer_group)
            
            # Start consumer task
            task_key = f"{channel}:{consumer_group}:{consumer_name}"
            if task_key not in self._subscription_tasks:
                task = asyncio.create_task(
                    self._consume_messages(
                        channel, consumer_group, consumer_name, message_handler
                    )
                )
                self._subscription_tasks[task_key] = task
                logger.info(f"Started subscription for {task_key}")
            
        except Exception as e:
            logger.error(f"Error subscribing to conversation: {e}")
            raise
    
    async def _consume_messages(
        self,
        stream: str,
        group_name: str,
        consumer_name: str,
        message_handler: Callable[[Message], None]
    ) -> None:
        """Internal message consumption loop."""
        try:
            while True:
                try:
                    # Read messages from stream
                    result = await self.redis_client.xreadgroup(
                        group_name,
                        consumer_name,
                        {stream: ">"},
                        count=10,
                        block=1000  # Block for 1 second
                    )
                    
                    if result:
                        for stream_name, messages in result:
                            for message_id, fields in messages:
                                try:
                                    # Parse message
                                    message = Message(
                                        id=fields["id"],
                                        conversation_id=fields["conversation_id"],
                                        sender=fields["sender"],
                                        content=fields["content"],
                                        turn=int(fields["turn"]),
                                        timestamp=fields["timestamp"],
                                        metadata=json.loads(fields.get("metadata", "{}"))
                                    )
                                    
                                    # Handle message
                                    await message_handler(message)
                                    
                                    # Acknowledge message
                                    await self.redis_client.xack(
                                        stream, group_name, message_id
                                    )
                                    
                                except Exception as e:
                                    logger.error(f"Error processing message {message_id}: {e}")
                                    continue
                
                except asyncio.CancelledError:
                    logger.info(f"Consumer {consumer_name} cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in message consumption: {e}")
                    await asyncio.sleep(1)  # Wait before retrying
                    
        except asyncio.CancelledError:
            logger.info(f"Message consumer {consumer_name} stopped")
    
    async def unsubscribe_from_conversation(
        self,
        channel: str,
        consumer_group: str,
        consumer_name: str
    ) -> None:
        """Unsubscribe from conversation updates."""
        task_key = f"{channel}:{consumer_group}:{consumer_name}"
        
        if task_key in self._subscription_tasks:
            task = self._subscription_tasks[task_key]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self._subscription_tasks[task_key]
            logger.info(f"Unsubscribed from {task_key}")
    
    async def get_active_conversations(self) -> List[str]:
        """Get list of active conversation channels."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            # Find all chat:* streams
            chat_streams = await self.redis_client.keys("chat:*")
            active_streams = []
            
            for stream in chat_streams:
                # Check if stream exists and has messages
                length = await self.redis_client.xlen(stream)
                if length > 0:
                    active_streams.append(stream)
            
            return active_streams
            
        except Exception as e:
            logger.error(f"Error getting active conversations: {e}")
            return []
    
    async def get_stream_info(self, stream: str) -> Dict[str, Any]:
        """Get detailed information about a stream."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            info = await self.redis_client.xinfo_stream(stream)
            return {
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": info.get("groups", 0)
            }
        except Exception as e:
            logger.error(f"Error getting stream info for {stream}: {e}")
            return {}
    
    async def get_consumer_group_info(self, stream: str) -> List[Dict[str, Any]]:
        """Get information about consumer groups for a stream."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            groups = await self.redis_client.xinfo_groups(stream)
            return [
                {
                    "name": group["name"],
                    "consumers": group["consumers"],
                    "pending": group["pending"],
                    "last_delivered_id": group["last-delivered-id"]
                }
                for group in groups
            ]
        except Exception as e:
            logger.error(f"Error getting consumer group info for {stream}: {e}")
            return []
    
    async def cleanup_old_conversations(self, max_age_hours: int = 24) -> int:
        """
        Clean up old conversation streams based on last activity.
        """
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            cleaned_count = 0
            current_time = asyncio.get_event_loop().time()
            max_age_seconds = max_age_hours * 3600
            
            # Get all chat streams
            chat_streams = await self.redis_client.keys("chat:*")
            
            for stream in chat_streams:
                try:
                    # Get last entry timestamp
                    last_entries = await self.redis_client.xrevrange(stream, count=1)
                    
                    if last_entries:
                        last_entry_id = last_entries[0][0]
                        # Extract timestamp from Redis stream ID (format: timestamp-sequence)
                        timestamp_ms = int(last_entry_id.split('-')[0])
                        timestamp_seconds = timestamp_ms / 1000
                        
                        age_seconds = current_time - timestamp_seconds
                        
                        if age_seconds > max_age_seconds:
                            # Delete old stream
                            deleted = await self.redis_client.delete(stream)
                            if deleted:
                                cleaned_count += 1
                                logger.info(f"Cleaned up old conversation stream: {stream}")
                    
                except Exception as e:
                    logger.warning(f"Error processing stream {stream} for cleanup: {e}")
                    continue
            
            logger.info(f"Cleaned up {cleaned_count} old conversation streams")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during conversation cleanup: {e}")
            return 0
    
    async def get_pending_messages(
        self,
        stream: str,
        group_name: str,
        consumer_name: str
    ) -> List[Dict[str, Any]]:
        """Get pending messages for a consumer."""
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            pending = await self.redis_client.xpending_range(
                stream, group_name, "-", "+", count=100
            )
            
            return [
                {
                    "message_id": item["message_id"],
                    "consumer": item["consumer"],
                    "time_since_delivered": item["time_since_delivered"],
                    "delivery_count": item["delivery_count"]
                }
                for item in pending
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending messages: {e}")
            return []
    
    async def stream_messages(
        self,
        channel: str,
        start_id: str = "$"
    ) -> AsyncGenerator[Message, None]:
        """
        Stream messages from a channel in real-time.
        """
        if not self.connected or not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            while True:
                result = await self.redis_client.xread({channel: start_id}, block=1000)
                
                if result:
                    for stream_name, messages in result:
                        for message_id, fields in messages:
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
                                
                                start_id = message_id  # Update for next read
                                yield message
                                
                            except Exception as e:
                                logger.warning(f"Failed to parse streamed message: {e}")
                                continue
                
        except asyncio.CancelledError:
            logger.info(f"Message streaming for {channel} cancelled")
        except Exception as e:
            logger.error(f"Error in message streaming: {e}")
            raise 