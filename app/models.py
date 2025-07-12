"""Data models for the poly-agents system."""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message in a conversation."""
    id: str
    conversation_id: str
    sender: str  # "user", "agent_0", "agent_1", etc., or "consensus"
    content: str
    turn: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ConsensusResult(BaseModel):
    """Result of consensus algorithm."""
    final_answer: str
    winning_votes: int
    total_votes: int
    consensus_method: str
    confidence_score: Optional[float] = None


class ConversationResult(BaseModel):
    """Complete conversation result for logging."""
    conversation_id: str
    prompt: str
    final_answer: str
    total_turns: int
    total_messages: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None


class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    """Response model for the /chat endpoint."""
    conversation_id: str
    response: str
    consensus_result: ConsensusResult

class ConversationListResponse(BaseModel):
    """Response for listing recent conversations."""
    conversations: list[dict]

class MessageSearchRequest(BaseModel):
    """Request for searching messages."""
    query: str
    top_k: int = 5

class AgentConfig(BaseModel):
    """Configuration for an individual agent."""
    agent_id: str
    model: str # Renamed from model_name to avoid pydantic conflict
    personality: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


class SystemHealth(BaseModel):
    """System health status."""
    status: str
    redis_connected: bool
    postgres_connected: bool
    qdrant_connected: bool = False
    active_conversations: int
    total_agents: int 