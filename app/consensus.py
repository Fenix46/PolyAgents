"""Consensus engine for reaching agreement among agents."""

import logging
from typing import List, Dict, Counter
from collections import Counter

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
import numpy as np

from .models import Message, ConsensusResult

logger = logging.getLogger(__name__)

# Load the sentence transformer model once
# Using a lightweight model for performance
transformer_model = SentenceTransformer('all-MiniLM-L6-v2')


class ConsensusEngine:
    """Pluggable consensus algorithm implementation."""
    
    def __init__(self, algorithm: str = "semantic"):
        self.algorithm = algorithm
        logger.info(f"ConsensusEngine initialized with algorithm: {self.algorithm}")
    
    async def reach_consensus(self, messages: List[Message]) -> ConsensusResult:
        """Apply consensus algorithm to agent messages."""
        if not messages:
            raise ValueError("Cannot reach consensus on empty message list")
        
        if self.algorithm == "majority_vote":
            return await self._majority_vote_consensus(messages)
        elif self.algorithm == "semantic":
            return await self._semantic_consensus(messages)
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
        embeddings = transformer_model.encode(contents)

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

    async def _old_semantic_consensus(self, messages: List[Message]) -> ConsensusResult:
        """
        Alternative consensus method using semantic similarity.
        TODO: Implement semantic clustering of responses.
        """
        raise NotImplementedError("Semantic consensus not yet implemented") 