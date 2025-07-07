"""Consensus engine for reaching agreement among agents."""

import logging
from typing import List, Dict, Counter
from collections import Counter

from .models import Message, ConsensusResult

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """Pluggable consensus algorithm implementation."""
    
    def __init__(self, algorithm: str = "majority_vote"):
        self.algorithm = algorithm
        logger.info(f"ConsensusEngine initialized with algorithm: {algorithm}")
    
    async def reach_consensus(self, messages: List[Message]) -> ConsensusResult:
        """Apply consensus algorithm to agent messages."""
        if not messages:
            raise ValueError("Cannot reach consensus on empty message list")
        
        if self.algorithm == "majority_vote":
            return await self._majority_vote_consensus(messages)
        else:
            raise ValueError(f"Unknown consensus algorithm: {self.algorithm}")
    
    async def _majority_vote_consensus(self, messages: List[Message]) -> ConsensusResult:
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
    
    async def _weighted_consensus(self, messages: List[Message]) -> ConsensusResult:
        """
        Alternative consensus method with agent weighting.
        TODO: Implement weighted voting based on agent confidence/history.
        """
        raise NotImplementedError("Weighted consensus not yet implemented")
    
    async def _semantic_consensus(self, messages: List[Message]) -> ConsensusResult:
        """
        Alternative consensus method using semantic similarity.
        TODO: Implement semantic clustering of responses.
        """
        raise NotImplementedError("Semantic consensus not yet implemented") 