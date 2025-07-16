"""Agent implementation with Gemini model integration."""

import asyncio
import logging
import os

import google.generativeai as genai

from .config import settings
from .memory.redis_bus import RedisBus
from .models import Message

logger = logging.getLogger(__name__)


class Agent:
    """Individual agent that wraps Gemini model calls."""

    def __init__(
        self,
        agent_id: str,
        model: str,
        redis_bus: RedisBus,
        personality: str | None = None,
        temperature: float | None = None
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
            "agent_0": """You are Agent 0, a logical and analytical thinker. Your role is to:
- Focus on facts, evidence, and systematic analysis
- Break down complex problems into logical components
- Provide structured, step-by-step reasoning
- Identify potential risks and technical challenges
- Be thorough and methodical in your approach
Always provide complete, well-reasoned responses.""",

            "agent_1": """You are Agent 1, a creative and innovative thinker. Your role is to:
- Think outside the box and propose novel solutions
- Focus on opportunities and possibilities
- Consider unconventional approaches and ideas
- Be optimistic but realistic about potential
- Provide imaginative yet practical insights
Always provide complete, creative responses.""",

            "agent_2": """You are Agent 2, a critical thinker and skeptic. Your role is to:
- Question assumptions and challenge conventional wisdom
- Identify potential problems and pitfalls
- Consider alternative perspectives and viewpoints
- Be thorough in examining potential issues
- Provide balanced, critical analysis
Always provide complete, critical responses.""",

            "agent_3": """You are Agent 3, a practical implementation specialist. Your role is to:
- Focus on feasibility and practical implementation
- Consider real-world constraints and limitations
- Provide actionable recommendations and next steps
- Think about scalability and maintainability
- Be pragmatic and solution-oriented
Always provide complete, practical responses."""
        }
        return personalities.get(self.agent_id, "You are a helpful AI assistant who provides complete, thoughtful responses.")

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

    async def generate_response(self, conversation_history: list[Message]) -> str:
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
                f"\nAs {self.agent_id}, provide your unique perspective on the conversation. "
                f"Consider the views of other agents but maintain your distinct personality and approach. "
                f"Provide a complete, thoughtful response that reflects your specific role and expertise. "
                f"Be thorough and ensure your response is complete - do not cut off mid-thought."
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
        """Process incoming message from Redis stream with simulated streaming."""
        logger.debug(f"Agent {self.agent_id} received message in {channel}: {message.id}")
        # Recupera callback di streaming se presente
        send_chunk = None
        if message.metadata and 'send_chunk' in message.metadata:
            send_chunk = message.metadata['send_chunk']
        # Genera risposta completa
        response = await self.generate_response([message])
        # Simula tokenizzazione (split per parola)
        tokens = response.split()
        buffer = []
        buffer_size = 10  # invia ogni 10 token
        for _i, token in enumerate(tokens):
            buffer.append(token)
            if len(buffer) >= buffer_size:
                chunk = ' '.join(buffer)
                if send_chunk:
                    await send_chunk(chunk)
                else:
                    logger.debug(f"[Stream] {chunk}")
                buffer = []
                await asyncio.sleep(0.05)  # Simula back-pressure
        # Flush finale
        if buffer:
            chunk = ' '.join(buffer)
            if send_chunk:
                await send_chunk(chunk)
            else:
                logger.debug(f"[Stream] {chunk}")
        # Segnala fine streaming
        if send_chunk:
            await send_chunk("[END]")
        logger.debug(f"Agent {self.agent_id} finished streaming for message {message.id}")
