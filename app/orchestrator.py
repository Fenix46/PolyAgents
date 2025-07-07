"""Orchestrator for managing multi-agent conversations."""

import asyncio
import logging
from typing import List, Dict, Any
from uuid import uuid4

from .agent import Agent
from .consensus import ConsensusEngine
from .memory.redis_bus import RedisBus
from .memory.postgres_log import PostgresLogger
from .models import Message, ConversationResult
from .config import settings

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates multi-agent conversations and consensus building."""
    
    def __init__(self):
        self.redis_bus = RedisBus()
        self.postgres_logger = PostgresLogger()
        self.consensus_engine = ConsensusEngine()
        self.agents: List[Agent] = []
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize all components."""
        if self.initialized:
            return
            
        await self.redis_bus.connect()
        await self.postgres_logger.connect()
        
        # Create agents with specific model configurations
        agent_configs = settings.get_agent_configs()
        
        for config in agent_configs:
            agent = Agent(
                agent_id=config.agent_id,
                model_name=config.model,
                redis_bus=self.redis_bus,
                personality=config.personality,
                temperature=config.temperature
            )
            self.agents.append(agent)
            logger.info(f"Created {config.agent_id} with model {config.model} (temp={config.temperature})")
        
        self.initialized = True
        logger.info(f"Orchestrator initialized with {len(self.agents)} agents using different models")
    
    async def cleanup(self) -> None:
        """Clean up connections."""
        await self.redis_bus.disconnect()
        await self.postgres_logger.disconnect()
        self.initialized = False
    
    async def run_conversation(
        self, 
        prompt: str, 
        conversation_id: str,
        n_turns: int = 2
    ) -> str:
        """
        Main orchestration logic:
        1. Broadcast initial prompt to all agents
        2. Run N turns of agent responses
        3. Apply consensus algorithm
        4. Log everything to postgres
        5. Return final answer
        """
        if not self.initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        channel = f"chat:{conversation_id}"
        messages: List[Message] = []
        
        try:
            # Log initial prompt
            initial_msg = Message(
                id=str(uuid4()),
                conversation_id=conversation_id,
                sender="user",
                content=prompt,
                turn=0
            )
            messages.append(initial_msg)
            await self.postgres_logger.log_message(initial_msg)
            
            # Broadcast initial prompt to Redis
            await self.redis_bus.send_message(channel, initial_msg)
            
            # Run conversation turns
            for turn in range(1, n_turns + 1):
                logger.info(f"Starting turn {turn} for conversation {conversation_id}")
                
                # Get responses from all agents in parallel
                agent_tasks = [
                    self._get_agent_response(agent, channel, conversation_id, turn)
                    for agent in self.agents
                ]
                
                agent_responses = await asyncio.gather(*agent_tasks, return_exceptions=True)
                
                # Filter out exceptions and collect valid responses
                valid_responses = [
                    resp for resp in agent_responses 
                    if isinstance(resp, Message)
                ]
                
                if not valid_responses:
                    raise RuntimeError(f"No valid agent responses in turn {turn}")
                
                # Log all agent responses
                for response in valid_responses:
                    messages.append(response)
                    await self.postgres_logger.log_message(response)
                    await self.redis_bus.send_message(channel, response)
                
                logger.info(f"Turn {turn} completed with {len(valid_responses)} responses")
            
            # Apply consensus algorithm to final turn responses
            final_turn_messages = [
                msg for msg in messages 
                if msg.turn == n_turns and msg.sender.startswith("agent_")
            ]
            
            consensus_result = await self.consensus_engine.reach_consensus(
                final_turn_messages
            )
            
            # Log consensus result
            consensus_msg = Message(
                id=str(uuid4()),
                conversation_id=conversation_id,
                sender="consensus",
                content=consensus_result.final_answer,
                turn=n_turns + 1
            )
            messages.append(consensus_msg)
            await self.postgres_logger.log_message(consensus_msg)
            
            # Store conversation result
            result = ConversationResult(
                conversation_id=conversation_id,
                prompt=prompt,
                final_answer=consensus_result.final_answer,
                total_turns=n_turns,
                total_messages=len(messages)
            )
            await self.postgres_logger.log_conversation_result(result)
            
            return consensus_result.final_answer
            
        except Exception as e:
            logger.error(f"Error in conversation {conversation_id}: {e}")
            raise
    
    async def _get_agent_response(
        self, 
        agent: Agent, 
        channel: str, 
        conversation_id: str,
        turn: int
    ) -> Message:
        """Get response from a single agent."""
        try:
            # Get conversation history from Redis
            history = await self.redis_bus.get_conversation_history(channel)
            
            # Generate agent response
            response_content = await agent.generate_response(history)
            
            # Create message
            message = Message(
                id=str(uuid4()),
                conversation_id=conversation_id,
                sender=agent.agent_id,
                content=response_content,
                turn=turn
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error getting response from {agent.agent_id}: {e}")
            raise 