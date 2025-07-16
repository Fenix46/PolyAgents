"""PostgreSQL logger for audit trail and conversation persistence."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..config import settings
from ..models import ConversationResult, Message

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy base class."""
    pass


class MessageRecord(Base):
    """Database model for messages."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    sender: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    turn: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    message_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ConversationRecord(Base):
    """Database model for conversation results."""
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(String, primary_key=True)
    prompt: Mapped[str] = mapped_column(Text)
    final_answer: Mapped[str] = mapped_column(Text)
    total_turns: Mapped[int] = mapped_column(Integer)
    total_messages: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)


class PostgresLogger:
    """PostgreSQL-based audit logger for conversations."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.connected = False

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        try:
            # Create async engine
            database_url = (
                f"postgresql+asyncpg://{settings.postgres_user}:"
                f"{settings.postgres_password}@{settings.postgres_host}:"
                f"{settings.postgres_port}/{settings.postgres_db}"
            )

            self.engine = create_async_engine(
                database_url,
                echo=settings.postgres_echo,
                pool_size=10,
                max_overflow=20
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.connected = True
            logger.info("Connected to PostgreSQL")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self.engine:
            await self.engine.dispose()
            self.connected = False
            logger.info("Disconnected from PostgreSQL")

    async def cleanup(self) -> None:
        """Clean up the PostgreSQL logger (alias for disconnect)."""
        await self.disconnect()

    async def log_message(self, message: Message) -> None:
        """Log a message to the database."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                message_record = MessageRecord(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    sender=message.sender,
                    content=message.content,
                    turn=message.turn,
                    timestamp=message.timestamp,
                    message_metadata=message.metadata
                )

                session.add(message_record)
                await session.commit()

            logger.debug(f"Logged message {message.id} to database")

        except Exception as e:
            logger.error(f"Error logging message to database: {e}")
            raise

    async def log_conversation_result(self, result: ConversationResult) -> None:
        """Log conversation result to the database."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                conversation_record = ConversationRecord(
                    conversation_id=result.conversation_id,
                    prompt=result.prompt,
                    final_answer=result.final_answer,
                    total_turns=result.total_turns,
                    total_messages=result.total_messages,
                    created_at=result.created_at,
                    duration_seconds=result.duration_seconds
                )

                session.add(conversation_record)
                await session.commit()

            logger.info(f"Logged conversation result {result.conversation_id} to database")

        except Exception as e:
            logger.error(f"Error logging conversation result to database: {e}")
            raise

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int | None = None,
        offset: int = 0
    ) -> list[Message]:
        """Retrieve all messages for a conversation."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                query = (
                    select(MessageRecord)
                    .where(MessageRecord.conversation_id == conversation_id)
                    .order_by(MessageRecord.timestamp)
                    .offset(offset)
                )

                if limit:
                    query = query.limit(limit)

                result = await session.execute(query)
                message_records = result.scalars().all()

                messages = [
                    Message(
                        id=record.id,
                        conversation_id=record.conversation_id,
                        sender=record.sender,
                        content=record.content,
                        turn=record.turn,
                        timestamp=record.timestamp,
                        metadata=record.message_metadata
                    )
                    for record in message_records
                ]

                logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
                return messages

        except Exception as e:
            logger.error(f"Error retrieving conversation messages: {e}")
            raise

    async def get_conversation_by_id(self, conversation_id: str) -> ConversationResult | None:
        """Get a specific conversation result by ID."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                query = select(ConversationRecord).where(
                    ConversationRecord.conversation_id == conversation_id
                )

                result = await session.execute(query)
                record = result.scalar_one_or_none()

                if record:
                    return ConversationResult(
                        conversation_id=record.conversation_id,
                        prompt=record.prompt,
                        final_answer=record.final_answer,
                        total_turns=record.total_turns,
                        total_messages=record.total_messages,
                        created_at=record.created_at,
                        duration_seconds=record.duration_seconds
                    )

                return None

        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}")
            raise

    async def get_recent_conversations(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> list[ConversationResult]:
        """Get recent conversations."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                query = (
                    select(ConversationRecord)
                    .order_by(desc(ConversationRecord.created_at))
                    .limit(limit)
                    .offset(offset)
                )

                result = await session.execute(query)
                records = result.scalars().all()

                conversations = [
                    ConversationResult(
                        conversation_id=record.conversation_id,
                        prompt=record.prompt,
                        final_answer=record.final_answer,
                        total_turns=record.total_turns,
                        total_messages=record.total_messages,
                        created_at=record.created_at,
                        duration_seconds=record.duration_seconds
                    )
                    for record in records
                ]

                logger.debug(f"Retrieved {len(conversations)} recent conversations")
                return conversations

        except Exception as e:
            logger.error(f"Error retrieving recent conversations: {e}")
            raise

    async def search_conversations(
        self,
        search_term: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[ConversationResult]:
        """Search conversations by prompt or answer content."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                query = (
                    select(ConversationRecord)
                    .where(
                        ConversationRecord.prompt.ilike(f"%{search_term}%") |
                        ConversationRecord.final_answer.ilike(f"%{search_term}%")
                    )
                    .order_by(desc(ConversationRecord.created_at))
                    .limit(limit)
                    .offset(offset)
                )

                result = await session.execute(query)
                records = result.scalars().all()

                conversations = [
                    ConversationResult(
                        conversation_id=record.conversation_id,
                        prompt=record.prompt,
                        final_answer=record.final_answer,
                        total_turns=record.total_turns,
                        total_messages=record.total_messages,
                        created_at=record.created_at,
                        duration_seconds=record.duration_seconds
                    )
                    for record in records
                ]

                logger.debug(f"Found {len(conversations)} conversations matching '{search_term}'")
                return conversations

        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            raise

    async def get_conversation_statistics(self) -> dict[str, Any]:
        """Get overall conversation statistics."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                # Count total conversations
                total_conversations_query = select(ConversationRecord.conversation_id)
                total_conversations_result = await session.execute(total_conversations_query)
                total_conversations = len(total_conversations_result.scalars().all())

                # Count total messages
                total_messages_query = select(MessageRecord.id)
                total_messages_result = await session.execute(total_messages_query)
                total_messages = len(total_messages_result.scalars().all())

                # Get recent activity (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_conversations_query = select(ConversationRecord.conversation_id).where(
                    ConversationRecord.created_at >= yesterday
                )
                recent_conversations_result = await session.execute(recent_conversations_query)
                recent_conversations = len(recent_conversations_result.scalars().all())

                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "recent_conversations_24h": recent_conversations,
                    "average_messages_per_conversation": (
                        total_messages / total_conversations if total_conversations > 0 else 0
                    )
                }

        except Exception as e:
            logger.error(f"Error getting conversation statistics: {e}")
            raise

    async def get_agent_statistics(self) -> dict[str, Any]:
        """Get statistics by agent."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                # Get message counts by agent using SQLAlchemy
                from sqlalchemy import func

                query = (
                    select(MessageRecord.sender, func.count(MessageRecord.id).label('message_count'))
                    .where(MessageRecord.sender.like('agent_%'))
                    .group_by(MessageRecord.sender)
                    .order_by(func.count(MessageRecord.id).desc())
                )

                result = await session.execute(query)
                agent_stats = {row[0]: row[1] for row in result.fetchall()}

                return {
                    "agent_message_counts": agent_stats,
                    "total_agent_messages": sum(agent_stats.values())
                }

        except Exception as e:
            logger.error(f"Error getting agent statistics: {e}")
            return {"agent_message_counts": {}, "total_agent_messages": 0}

    async def cleanup_old_data(self, days_to_keep: int = 30) -> dict[str, int]:
        """
        Clean up old conversation data.
        """
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            cleaned_counts = {"messages": 0, "conversations": 0}

            async with self.session_factory() as session:
                # First, get conversation IDs to delete
                old_conversations_query = select(ConversationRecord.conversation_id).where(
                    ConversationRecord.created_at < cutoff_date
                )
                result = await session.execute(old_conversations_query)
                old_conversation_ids = [row[0] for row in result.fetchall()]

                if old_conversation_ids:
                    # Delete messages for old conversations
                    delete_messages_query = delete(MessageRecord).where(
                        MessageRecord.conversation_id.in_(old_conversation_ids)
                    )
                    messages_result = await session.execute(delete_messages_query)
                    cleaned_counts["messages"] = messages_result.rowcount

                    # Delete old conversations
                    delete_conversations_query = delete(ConversationRecord).where(
                        ConversationRecord.conversation_id.in_(old_conversation_ids)
                    )
                    conversations_result = await session.execute(delete_conversations_query)
                    cleaned_counts["conversations"] = conversations_result.rowcount

                    await session.commit()

                logger.info(
                    f"Cleaned up {cleaned_counts['conversations']} conversations and "
                    f"{cleaned_counts['messages']} messages older than {days_to_keep} days"
                )

                return cleaned_counts

        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            raise

    async def get_conversation_timeline(
        self,
        conversation_id: str
    ) -> dict[str, Any]:
        """Get detailed timeline of a conversation."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                # Get conversation info
                conversation = await self.get_conversation_by_id(conversation_id)
                if not conversation:
                    return {"error": "Conversation not found"}

                # Get all messages
                messages = await self.get_conversation_messages(conversation_id)

                # Group messages by turn
                turns = {}
                for message in messages:
                    turn = message.turn
                    if turn not in turns:
                        turns[turn] = []
                    turns[turn].append({
                        "id": message.id,
                        "sender": message.sender,
                        "content": message.content,
                        "timestamp": message.timestamp.isoformat(),
                        "metadata": message.metadata
                    })

                return {
                    "conversation": {
                        "id": conversation.conversation_id,
                        "prompt": conversation.prompt,
                        "final_answer": conversation.final_answer,
                        "total_turns": conversation.total_turns,
                        "total_messages": conversation.total_messages,
                        "created_at": conversation.created_at.isoformat(),
                        "duration_seconds": conversation.duration_seconds
                    },
                    "timeline": [
                        {
                            "turn": turn_num,
                            "messages": turn_messages
                        }
                        for turn_num, turn_messages in sorted(turns.items())
                    ]
                }

        except Exception as e:
            logger.error(f"Error getting conversation timeline: {e}")
            raise

    async def export_conversations(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        format: str = "json"
    ) -> list[dict[str, Any]]:
        """Export conversations for backup or analysis."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")

        try:
            async with self.session_factory() as session:
                query = select(ConversationRecord)

                if start_date:
                    query = query.where(ConversationRecord.created_at >= start_date)
                if end_date:
                    query = query.where(ConversationRecord.created_at <= end_date)

                query = query.order_by(ConversationRecord.created_at)

                result = await session.execute(query)
                records = result.scalars().all()

                exported_data = []
                for record in records:
                    # Get messages for this conversation
                    messages = await self.get_conversation_messages(record.conversation_id)

                    exported_data.append({
                        "conversation": {
                            "id": record.conversation_id,
                            "prompt": record.prompt,
                            "final_answer": record.final_answer,
                            "total_turns": record.total_turns,
                            "total_messages": record.total_messages,
                            "created_at": record.created_at.isoformat(),
                            "duration_seconds": record.duration_seconds
                        },
                        "messages": [
                            {
                                "id": msg.id,
                                "sender": msg.sender,
                                "content": msg.content,
                                "turn": msg.turn,
                                "timestamp": msg.timestamp.isoformat(),
                                "metadata": msg.metadata
                            }
                            for msg in messages
                        ]
                    })

                logger.info(f"Exported {len(exported_data)} conversations")
                return exported_data

        except Exception as e:
            logger.error(f"Error exporting conversations: {e}")
            raise
