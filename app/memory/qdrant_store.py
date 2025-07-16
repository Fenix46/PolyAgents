"""Qdrant vector store for long-term conversation memory."""

import asyncio
import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer

from ..config import settings

logger = logging.getLogger(__name__)


class QdrantStore:
    """
    Qdrant-based vector store for semantic conversation memory.
    Optional component for long-term memory and conversation similarity.
    """

    def __init__(self):
        self.client: QdrantClient | None = None
        self.collection_name = "conversation_memory"
        self.connected = False
        # Carica modello embedding una sola volta
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None

    async def initialize(self) -> None:
        """Initialize the Qdrant store (alias for connect)."""
        await self.connect()

    async def connect(self) -> None:
        """Connect to Qdrant."""
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=10
            )

            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.get_collections
            )

            # Create collection if it doesn't exist
            await self._ensure_collection_exists()

            self.connected = True
            logger.info("Connected to Qdrant")

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from Qdrant."""
        if self.client:
            # Qdrant client doesn't need explicit disconnection
            self.client = None
            self.connected = False
            logger.info("Disconnected from Qdrant")

    async def cleanup(self) -> None:
        """Clean up the Qdrant store (alias for disconnect)."""
        await self.disconnect()

    async def _ensure_collection_exists(self) -> None:
        """Ensure the conversation memory collection exists."""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")

        try:
            # Check if collection exists
            collections = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.get_collections
            )

            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with vector configuration
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.client.create_collection,
                    self.collection_name,
                    VectorParams(
                        size=settings.qdrant_vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    async def store_conversation_embedding(
        self,
        conversation_id: str,
        conversation_summary: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Store conversation embedding for semantic search."""
        if not self.connected or not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            point = models.PointStruct(
                id=conversation_id,
                vector=embedding,
                payload={
                    "conversation_id": conversation_id,
                    "summary": conversation_summary,
                    "metadata": metadata or {}
                }
            )

            await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.upsert,
                self.collection_name,
                [point]
            )

            logger.debug(f"Stored embedding for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error storing conversation embedding: {e}")
            raise

    async def search_similar_conversations(
        self,
        query_embedding: list[float],
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """Search for similar conversations based on semantic similarity."""
        if not self.connected or not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.client.search,
                self.collection_name,
                query_embedding,
                limit,
                score_threshold
            )

            similar_conversations = []
            for hit in search_result:
                similar_conversations.append({
                    "conversation_id": hit.payload["conversation_id"],
                    "summary": hit.payload["summary"],
                    "similarity_score": hit.score,
                    "metadata": hit.payload.get("metadata", {})
                })

            logger.debug(f"Found {len(similar_conversations)} similar conversations")
            return similar_conversations

        except Exception as e:
            logger.error(f"Error searching similar conversations: {e}")
            return []

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using SentenceTransformer.
        """
        if not self.embedding_model:
            logger.error("Embedding model not loaded, returning dummy vector")
            return [0.0] * 384  # fallback size
        try:
            # SentenceTransformer è sincrono, usiamo thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, self.embedding_model.encode, text)
            return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * 384

    async def get_conversation_context(
        self,
        current_prompt: str,
        max_context_conversations: int = 3
    ) -> list[dict[str, Any]]:
        """
        Get relevant conversation context for current prompt using semantic similarity.
        """
        if not self.connected or not self.client:
            logger.warning("Qdrant not connected, returning empty context")
            return []
        try:
            query_embedding = await self.generate_embedding(current_prompt)
            similar = await self.search_similar_conversations(query_embedding, limit=max_context_conversations)
            return similar
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

    async def cleanup_old_embeddings(self, days_to_keep: int = 90) -> int:
        """
        Clean up old conversation embeddings.
        TODO: Implement based on timestamp metadata.
        """
        raise NotImplementedError("Embedding cleanup not yet implemented")
