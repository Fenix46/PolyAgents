"""Consensus engine for reaching agreement among agents."""

import logging
from collections import Counter

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import os

from .agent import Agent  # Importiamo Agent per usare il LLM
from .models import ConsensusResult, Message
from .config import settings

logger = logging.getLogger(__name__)

# Caricamento modello locale parametrico
_local_model = None
_local_tokenizer = None
_local_pipe = None

def get_local_llm():
    global _local_model, _local_tokenizer, _local_pipe
    if _local_model is None or _local_tokenizer is None or _local_pipe is None:
        token = os.getenv("HUGGINGFACE_TOKEN")
        _local_tokenizer = AutoTokenizer.from_pretrained(settings.local_llm_model, token=token)
        _local_model = AutoModelForCausalLM.from_pretrained(settings.local_llm_model, token=token)
        _local_pipe = pipeline("text-generation", model=_local_model, tokenizer=_local_tokenizer)
    return _local_pipe

# Per embedding, se serve, si può usare pipeline("feature-extraction", ...)


class ConsensusEngine:
    """Pluggable consensus algorithm implementation."""

    def __init__(self, algorithm: str = "semantic"):
        self.algorithm = algorithm
        logger.info(f"ConsensusEngine initialized with algorithm: {self.algorithm}")

    async def reach_consensus(self, messages: list[Message]) -> ConsensusResult:
        """Apply consensus algorithm to agent messages."""
        if not messages:
            raise ValueError("Cannot reach consensus on empty message list")

        if self.algorithm == "majority_vote":
            return await self._majority_vote_consensus(messages)
        elif self.algorithm == "semantic":
            return await self._semantic_consensus(messages)
        elif self.algorithm == "synthesis":
            return await self._synthesis_consensus(messages)
        else:
            raise ValueError(f"Unknown consensus algorithm: {self.algorithm}")

    async def _majority_vote_consensus(self, messages: list[Message]) -> ConsensusResult:
        """
        Majority vote consensus with tie-breaking:
        1. Vote on first line of each message
        2. In case of tie, use longest message
        3. In case of equal length, use first message alphabetically
        """
        if len(messages) == 1:
            return ConsensusResult(
                final_answer=messages[0].content,
                winning_votes=1,
                total_votes=1,
                consensus_method="single_response"
            )

        # Extract first lines for voting
        first_lines = []
        message_map = {}

        for msg in messages:
            first_line = msg.content.strip().split('\n')[0]
            first_lines.append(first_line)

            # Map first line to full message for tie-breaking
            if first_line not in message_map:
                message_map[first_line] = []
            message_map[first_line].append(msg)

        # Count votes
        vote_counts = Counter(first_lines)
        max_votes = max(vote_counts.values())

        # Find all options with maximum votes
        top_options = [
            option for option, count in vote_counts.items()
            if count == max_votes
        ]

        if len(top_options) == 1:
            # Clear winner
            winning_option = top_options[0]
            winning_message = message_map[winning_option][0]

        else:
            # Tie-breaking: choose longest message among tied options
            tie_breaker_candidates = []
            for option in top_options:
                for msg in message_map[option]:
                    tie_breaker_candidates.append((len(msg.content), msg.content, msg))

            # Sort by length (desc), then alphabetically (asc)
            tie_breaker_candidates.sort(key=lambda x: (-x[0], x[1]))
            winning_message = tie_breaker_candidates[0][2]
            winning_option = winning_message.content.strip().split('\n')[0]

        logger.info(
            f"Consensus reached: '{winning_option[:50]}...' "
            f"with {max_votes}/{len(messages)} votes"
        )

        return ConsensusResult(
            final_answer=winning_message.content,
            winning_votes=max_votes,
            total_votes=len(messages),
            consensus_method="majority_vote_with_tiebreak"
        )

    async def _weighted_consensus(self, messages: list[Message]) -> ConsensusResult:
        """
        Weighted majority vote consensus: ogni agente vota con un peso (es. confidence, reliability).
        1. Somma i pesi per ciascuna risposta (prima riga del messaggio).
        2. In caso di parità, tie-break come in majority_vote.
        """
        if len(messages) == 1:
            return ConsensusResult(
                final_answer=messages[0].content,
                winning_votes=1,
                total_votes=1,
                consensus_method="single_response"
            )

        first_lines = []
        message_map = {}
        weight_map = {}

        for msg in messages:
            first_line = msg.content.strip().split('\n')[0]
            first_lines.append(first_line)
            # Map first line to full message for tie-breaking
            if first_line not in message_map:
                message_map[first_line] = []
            message_map[first_line].append(msg)
            # Somma i pesi (default 1 se non presente)
            weight = getattr(msg, 'weight', 1)
            weight_map[first_line] = weight_map.get(first_line, 0) + weight

        # Trova il massimo peso
        max_weight = max(weight_map.values())
        top_options = [option for option, w in weight_map.items() if w == max_weight]

        if len(top_options) == 1:
            winning_option = top_options[0]
            winning_message = message_map[winning_option][0]
        else:
            # Tie-break: scegli il messaggio più lungo tra i candidati
            tie_breaker_candidates = []
            for option in top_options:
                for msg in message_map[option]:
                    tie_breaker_candidates.append((len(msg.content), msg.content, msg))
            tie_breaker_candidates.sort(key=lambda x: (-x[0], x[1]))
            winning_message = tie_breaker_candidates[0][2]
            winning_option = winning_message.content.strip().split('\n')[0]

        logger.info(
            f"Weighted consensus: '{winning_option[:50]}...' with {max_weight} weighted votes out of {len(messages)} messages"
        )

        return ConsensusResult(
            final_answer=winning_message.content,
            winning_votes=max_weight,
            total_votes=len(messages),
            consensus_method="weighted_majority_vote"
        )

    async def _semantic_consensus(self, messages: list[Message]) -> ConsensusResult:
        """
        Reaches consensus by clustering message embeddings.
        1. Encodes all messages into vector embeddings.
        2. Uses K-Means to cluster the messages.
        3. Finds the largest cluster.
        4. Selects the message closest to the cluster's center as the winner.
        """
        if len(messages) == 1:
            return ConsensusResult(
                final_answer=messages[0].content,
                winning_votes=1,
                total_votes=1,
                consensus_method="single_response"
            )

        contents = [msg.content for msg in messages]
        embeddings = get_local_llm().encode(contents)

        # Determine the optimal number of clusters (k)
        # We can't have more clusters than messages
        n_clusters = min(len(messages) // 2, 5)
        if n_clusters < 2:
            n_clusters = 2
        if n_clusters > len(messages):
            n_clusters = len(messages)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto').fit(embeddings)

        # Find the largest cluster
        largest_cluster_label = Counter(kmeans.labels_).most_common(1)[0][0]

        # Get all messages and embeddings from the largest cluster
        cluster_indices = [i for i, label in enumerate(kmeans.labels_) if label == largest_cluster_label]
        cluster_embeddings = np.array([embeddings[i] for i in cluster_indices])

        # Find the message closest to the center of the largest cluster
        centroid = kmeans.cluster_centers_[largest_cluster_label]
        closest_message_index_in_cluster, _ = pairwise_distances_argmin_min(
            [centroid], cluster_embeddings
        )

        # Get the original index of the winning message
        winning_message_index = cluster_indices[closest_message_index_in_cluster[0]]
        winning_message = messages[winning_message_index]

        winning_votes = len(cluster_indices)

        logger.info(
            f"Semantic consensus reached: message from {winning_message.sender} won "
            f"with {winning_votes}/{len(messages)} votes in its cluster."
        )

        return ConsensusResult(
            final_answer=winning_message.content,
            winning_votes=winning_votes,
            total_votes=len(messages),
            consensus_method="semantic_clustering"
        )

    def _summarize_with_local_llm(self, text: str) -> str:
        """Usa Qwen3-0.6B (thinking) per riassumere una risposta cloud."""
        pipe = get_local_llm()
        prompt = (
            "You are a thinking assistant. Summarize the following agent response in a concise, insightful way, highlighting the key points and reasoning steps.\n" + text
        )
        result = pipe(prompt, max_new_tokens=128, do_sample=False)
        return result[0]["generated_text"].strip()

    def _fuse_with_local_llm(self, summaries: list[str], user_prompt: str) -> str:
        """Usa Qwen3-0.6B (thinking) per fondere i riassunti in una risposta unica e intelligente."""
        pipe = get_local_llm()
        prompt = (
            "You are a thinking assistant. Given the original user question and the following agent summaries, synthesize a single, comprehensive answer that combines the best insights, resolves conflicts, and provides actionable recommendations.\n"
            f"User question: {user_prompt}\n"
            "Agent summaries:\n"
        )
        for i, summary in enumerate(summaries):
            prompt += f"Agent {i+1}: {summary}\n"
        prompt += "\nSynthesized answer:"
        result = pipe(prompt, max_new_tokens=256, do_sample=False)
        return result[0]["generated_text"].strip()

    async def _synthesis_consensus(self, messages: list[Message]) -> ConsensusResult:
        """
        Synthesis consensus che usa Qwen3-0.6B locale (thinking) per riassumere e fondere le risposte cloud.
        """
        if len(messages) == 1:
            return ConsensusResult(
                final_answer=messages[0].content,
                winning_votes=1,
                total_votes=1,
                consensus_method="single_response"
            )
        # Estrai prompt utente
        user_prompt = self._extract_user_prompt(messages)
        # Prendi solo le risposte degli agenti cloud (sender che inizia con 'agent_')
        agent_responses = [msg for msg in messages if msg.sender.startswith("agent_")]
        # Riassumi ogni risposta cloud con Qwen3-0.6B
        summaries = []
        for msg in agent_responses:
            summary = self._summarize_with_local_llm(msg.content)
            summaries.append(summary)
        # Fusione intelligente dei riassunti
        fused = self._fuse_with_local_llm(summaries, user_prompt)
        logger.info(f"Local synthesis consensus created from {len(agent_responses)} agent responses")
        return ConsensusResult(
            final_answer=fused,
            winning_votes=len(agent_responses),
            total_votes=len(messages),
            consensus_method="local_synthesis_qwen3-0.6b",
            confidence_score=0.9
        )

    def _create_synthesis_prompt(self, messages: list[Message]) -> str:
        """Create a prompt for synthesizing agent responses."""
        # Extract the original user prompt from the conversation
        user_prompt = self._extract_user_prompt(messages)

        prompt_parts = [
            "You are a consensus synthesizer. Your task is to create a comprehensive response that combines the best insights from multiple AI agents.",
            f"\n**Original User Question:** {user_prompt}",
            "\n**Agent responses to synthesize:"
        ]

        for i, msg in enumerate(messages):
            agent_name = msg.sender.replace("agent_", "Agent ")
            prompt_parts.append(f"\n**{agent_name}:**")
            prompt_parts.append(msg.content)

        prompt_parts.extend([
            "\n**Your Task:**",
            "1. **Directly answer the user's original question** using insights from all agents",
            "2. **Identify and combine the best ideas** from each agent's perspective",
            "3. **Create a comprehensive, well-structured response** that addresses all aspects of the question",
            "4. **Maintain depth and detail** while creating a coherent narrative",
            "5. **Provide actionable insights** and practical recommendations",
            "6. **Acknowledge different perspectives** but create a unified response",
            "7. **Be thorough and complete** - this should be a substantial response",
            "\n**Important:** Your response should be a complete answer to the user's question, not just a summary of what the agents said. Synthesize their insights into a coherent, actionable response.",
            "\n**Synthesized Response:**"
        ])

        return "\n".join(prompt_parts)

    def _extract_user_prompt(self, messages: list[Message]) -> str:
        """Extract the original user prompt from the conversation."""
        # Look for the user message (usually the first message in the conversation)
        for msg in messages:
            if msg.sender == "user":
                return msg.content

        # If no user message in the provided messages, try to get it from the conversation context
        # This might happen if we only pass agent responses to consensus
        if messages and hasattr(messages[0], 'conversation_id'):
            # We could potentially fetch the conversation history here
            # For now, return a generic message
            return "User's original question about the topic discussed"

        # Fallback if no user message found
        return "User's original question"

    def _simple_synthesis(self, messages: list[Message]) -> str:
        """Simple synthesis that combines key points from all agents."""
        synthesis_parts = [
            "Based on the analysis from multiple AI agents, here is a comprehensive synthesis:",
            "\n"
        ]

        # Extract key insights from each agent
        for _i, msg in enumerate(messages):
            agent_name = msg.sender.replace("agent_", "Agent ")
            synthesis_parts.append(f"**{agent_name}'s Perspective:**")

            # Take the first few sentences as key insights
            content_lines = msg.content.strip().split('\n')
            key_insights = content_lines[:3]  # First 3 lines as key insights

            for line in key_insights:
                if line.strip():
                    synthesis_parts.append(f"- {line.strip()}")

            synthesis_parts.append("")

        # Add synthesis conclusion
        synthesis_parts.extend([
            "**Synthesized Conclusion:**",
            "The combined analysis reveals multiple important dimensions of this topic. ",
            "The logical analysis provides a solid foundation, while the creative perspective opens new possibilities. ",
            "Critical thinking identifies potential challenges, and practical considerations ensure feasibility. ",
            "A successful approach would integrate these complementary perspectives, leveraging the strengths of each while addressing the concerns raised."
        ])

        return "\n".join(synthesis_parts)

    async def _llm_synthesis(self, prompt: str) -> str:
        """Use LLM to create intelligent synthesis of agent responses."""
        try:
            # Create a temporary consensus agent with a mock Redis bus
            class MockRedisBus:
                async def send_message(self, *args, **kwargs):
                    pass
                async def get_messages(self, *args, **kwargs):
                    return []

            consensus_agent = Agent(
                agent_id="consensus_synthesizer",
                model="gemini-pro",  # Use the same model as other agents
                redis_bus=MockRedisBus(),  # Mock Redis bus
                personality="""You are a consensus synthesizer. Your role is to:
- Analyze multiple AI agent responses to a user's question
- Identify the key insights and unique perspectives from each agent
- Combine complementary ideas and resolve conflicts intelligently
- Create a comprehensive, well-structured response that directly answers the user's original question
- Maintain the depth and detail of the original responses while creating a coherent narrative
- Focus on actionable insights and practical recommendations
- Be thorough and complete in your synthesis""",
                temperature=0.3  # Lower temperature for more focused synthesis
            )

            # Call the LLM
            response = await consensus_agent.call_gemini(prompt, "gemini-pro")
            return response.strip()

        except Exception as e:
            logger.error(f"Error in LLM synthesis: {e}")
            raise

    async def _old_semantic_consensus(self, messages: list[Message]) -> ConsensusResult:
        """
        Alternative consensus method using semantic similarity.
        TODO: Implement semantic clustering of responses.
        """
        raise NotImplementedError("Semantic consensus not yet implemented")
