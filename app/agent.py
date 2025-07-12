"""Agent implementation with Gemini model integration."""

import os
import logging
from typing import List, Optional
import asyncio

import google.generativeai as genai

from .models import Message
from .memory.redis_bus import RedisBus
from .config import settings

logger = logging.getLogger(__name__)


class Agent:
    """Individual agent that wraps Gemini model calls."""
    
    def __init__(
        self, 
        agent_id: str, 
        model: str,
        redis_bus: RedisBus,
        personality: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self.agent_id = agent_id
        self.model = model
        self.redis_bus = redis_bus
        self.personality = personality or self._get_default_personality()
        self.temperature = temperature or settings.gemini_temperature
        
        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        logger.info(f"Agent {agent_id} initialized with model {self.model} (temp={self.temperature})")
    
    def _get_default_personality(self) -> str:
        """Get default personality based on agent ID."""
        personalities = {
            "agent_0": "You are a logical and analytical thinker who focuses on facts and evidence.",
            "agent_1": "You are a creative and innovative thinker who looks for novel solutions.",
            "agent_2": "You are a critical thinker who questions assumptions and finds potential issues.",
            "agent_3": "You are a practical thinker who focuses on implementation and feasibility."
        }
        return personalities.get(self.agent_id, "You are a helpful AI assistant.")
    
    async def call_gemini(self, prompt: str, model_to_use: str) -> str:
        """Make async call to Gemini API."""
        try:
            # Use asyncio to run the sync Gemini call in a thread pool
            loop = asyncio.get_event_loop()
            
            def _sync_call():
                model = genai.GenerativeModel(model_to_use)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=settings.gemini_max_tokens,
                    )
                )
                return response.text
            
            result = await loop.run_in_executor(None, _sync_call)
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error calling Gemini for {self.agent_id}: {e}")
            raise
    
    async def generate_response(self, conversation_history: List[Message]) -> str:
        """Generate agent response based on conversation history."""
        try:
            # Build context from conversation history
            context_parts = [f"Agent Personality: {self.personality}\n"]
            
            for msg in conversation_history[-10:]:  # Use last 10 messages for context
                sender = msg.sender
                content = msg.content
                context_parts.append(f"{sender}: {content}")
            
            # Add instruction for the agent
            context_parts.append(
                f"\nAs {self.agent_id}, provide your perspective on the conversation. "
                f"Be concise but thoughtful, and consider the views of other agents."
            )
            
            full_prompt = "\n".join(context_parts)
            
            # Call Gemini
            response = await self.call_gemini(full_prompt, self.model)
            
            logger.debug(f"Agent {self.agent_id} generated response: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response for {self.agent_id}: {e}")
            # Return a fallback response
            return f"Agent {self.agent_id} encountered an error: {str(e)}"
    
    async def process_stream_message(self, channel: str, message: Message) -> None:
        """Process incoming message from Redis stream."""
        # TODO: Implement stream message processing for real-time responses
        logger.debug(f"Agent {self.agent_id} received message in {channel}: {message.id}")
        pass 