"""PostgreSQL logger for audit trail and conversation persistence."""

import logging
from typing import Optional, List
from datetime import datetime
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer, Text, JSON

from ..models import Message, ConversationResult
from ..config import settings

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
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ConversationRecord(Base):
    """Database model for conversation results."""
    __tablename__ = "conversations"
    
    conversation_id: Mapped[str] = mapped_column(String, primary_key=True)
    prompt: Mapped[str] = mapped_column(Text)
    final_answer: Mapped[str] = mapped_column(Text)
    total_turns: Mapped[int] = mapped_column(Integer)
    total_messages: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)


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
                    metadata=message.metadata
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
        conversation_id: str
    ) -> List[Message]:
        """Retrieve all messages for a conversation."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")
        
        try:
            async with self.session_factory() as session:
                # TODO: Implement SQLAlchemy query to get messages
                # This is a placeholder for the query logic
                raise NotImplementedError("Message retrieval not yet implemented")
                
        except Exception as e:
            logger.error(f"Error retrieving conversation messages: {e}")
            raise
    
    async def get_recent_conversations(
        self, 
        limit: int = 10
    ) -> List[ConversationResult]:
        """Get recent conversations."""
        if not self.connected or not self.session_factory:
            raise RuntimeError("PostgreSQL not connected")
        
        try:
            async with self.session_factory() as session:
                # TODO: Implement SQLAlchemy query for recent conversations
                raise NotImplementedError("Recent conversations query not yet implemented")
                
        except Exception as e:
            logger.error(f"Error retrieving recent conversations: {e}")
            raise
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        Clean up old conversation data.
        TODO: Implement data retention policy.
        """
        raise NotImplementedError("Data cleanup not yet implemented") 