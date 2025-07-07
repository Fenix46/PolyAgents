"""Tests for the orchestrator module."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.orchestrator import Orchestrator
from app.models import Message, ConsensusResult, ConversationResult


@pytest_asyncio.fixture
async def mock_orchestrator():
    """Create orchestrator with mocked dependencies."""
    with patch("app.orchestrator.RedisBus") as mock_redis, \
         patch("app.orchestrator.PostgresLogger") as mock_postgres, \
         patch("app.orchestrator.ConsensusEngine") as mock_consensus, \
         patch("app.orchestrator.Agent") as mock_agent_class, \
         patch("app.orchestrator.settings") as mock_settings:
        
        # Configure mock settings
        mock_settings.num_agents = 3
        mock_settings.gemini_model = "gemini-pro"
        
        # Configure mock dependencies
        mock_redis_instance = AsyncMock()
        mock_postgres_instance = AsyncMock()
        mock_consensus_instance = AsyncMock()
        
        mock_redis.return_value = mock_redis_instance
        mock_postgres.return_value = mock_postgres_instance
        mock_consensus.return_value = mock_consensus_instance
        
        # Configure mock agents
        mock_agents = []
        for i in range(3):
            mock_agent = AsyncMock()
            mock_agent.agent_id = f"agent_{i}"
            mock_agent.generate_response = AsyncMock(return_value=f"Response from agent {i}")
            mock_agents.append(mock_agent)
        
        mock_agent_class.side_effect = mock_agents
        
        # Create orchestrator
        orchestrator = Orchestrator()
        
        # Override the mocked instances
        orchestrator.redis_bus = mock_redis_instance
        orchestrator.postgres_logger = mock_postgres_instance
        orchestrator.consensus_engine = mock_consensus_instance
        
        yield orchestrator, {
            "redis": mock_redis_instance,
            "postgres": mock_postgres_instance,
            "consensus": mock_consensus_instance,
            "agents": mock_agents
        }


class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_orchestrator):
        """Test successful orchestrator initialization."""
        orchestrator, mocks = mock_orchestrator
        
        await orchestrator.initialize()
        
        assert orchestrator.initialized is True
        assert len(orchestrator.agents) == 3
        
        # Verify connections were established
        mocks["redis"].connect.assert_called_once()
        mocks["postgres"].connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, mock_orchestrator):
        """Test that initialize is idempotent."""
        orchestrator, mocks = mock_orchestrator
        
        await orchestrator.initialize()
        await orchestrator.initialize()  # Call again
        
        # Should only be called once
        mocks["redis"].connect.assert_called_once()
        mocks["postgres"].connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_orchestrator):
        """Test orchestrator cleanup."""
        orchestrator, mocks = mock_orchestrator
        
        await orchestrator.initialize()
        await orchestrator.cleanup()
        
        assert orchestrator.initialized is False
        mocks["redis"].disconnect.assert_called_once()
        mocks["postgres"].disconnect.assert_called_once()


class TestConversationFlow:
    """Tests for conversation orchestration."""
    
    @pytest.mark.asyncio
    async def test_run_conversation_success(self, mock_orchestrator):
        """Test successful conversation flow."""
        orchestrator, mocks = mock_orchestrator
        await orchestrator.initialize()
        
        # Mock consensus result
        consensus_result = ConsensusResult(
            final_answer="Consensus answer",
            winning_votes=2,
            total_votes=3,
            consensus_method="majority_vote"
        )
        mocks["consensus"].reach_consensus.return_value = consensus_result
        
        # Run conversation
        result = await orchestrator.run_conversation(
            prompt="Test prompt",
            conversation_id="test-conv-id",
            n_turns=2
        )
        
        assert result == "Consensus answer"
        
        # Verify Redis interactions
        assert mocks["redis"].send_message.call_count >= 1  # Initial prompt + responses
        mocks["redis"].get_conversation_history.assert_called()
        
        # Verify PostgreSQL logging
        assert mocks["postgres"].log_message.call_count >= 4  # Initial + 3 agents + consensus
        mocks["postgres"].log_conversation_result.assert_called_once()
        
        # Verify consensus was called
        mocks["consensus"].reach_consensus.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_conversation_not_initialized(self, mock_orchestrator):
        """Test conversation fails when not initialized."""
        orchestrator, mocks = mock_orchestrator
        
        with pytest.raises(RuntimeError, match="not initialized"):
            await orchestrator.run_conversation(
                prompt="Test prompt",
                conversation_id="test-conv-id"
            )
    
    @pytest.mark.asyncio
    async def test_run_conversation_no_valid_responses(self, mock_orchestrator):
        """Test conversation fails when no agents respond."""
        orchestrator, mocks = mock_orchestrator
        await orchestrator.initialize()
        
        # Make all agents fail
        for agent in mocks["agents"]:
            agent.generate_response.side_effect = Exception("Agent failed")
        
        with pytest.raises(RuntimeError, match="No valid agent responses"):
            await orchestrator.run_conversation(
                prompt="Test prompt",
                conversation_id="test-conv-id",
                n_turns=1
            )
    
    @pytest.mark.asyncio
    async def test_run_conversation_partial_agent_failure(self, mock_orchestrator):
        """Test conversation continues with some agent failures."""
        orchestrator, mocks = mock_orchestrator
        await orchestrator.initialize()
        
        # Make one agent fail
        mocks["agents"][0].generate_response.side_effect = Exception("Agent 0 failed")
        
        # Mock consensus result
        consensus_result = ConsensusResult(
            final_answer="Consensus from 2 agents",
            winning_votes=1,
            total_votes=2,
            consensus_method="majority_vote"
        )
        mocks["consensus"].reach_consensus.return_value = consensus_result
        
        result = await orchestrator.run_conversation(
            prompt="Test prompt",
            conversation_id="test-conv-id",
            n_turns=1
        )
        
        assert result == "Consensus from 2 agents"


class TestAgentResponseGeneration:
    """Tests for individual agent response generation."""
    
    @pytest.mark.asyncio
    async def test_get_agent_response_success(self, mock_orchestrator):
        """Test successful agent response generation."""
        orchestrator, mocks = mock_orchestrator
        await orchestrator.initialize()
        
        # Mock conversation history
        history = [
            Message(
                id="msg1",
                conversation_id="test-conv",
                sender="user",
                content="Hello",
                turn=0
            )
        ]
        mocks["redis"].get_conversation_history.return_value = history
        
        agent = mocks["agents"][0]
        response = await orchestrator._get_agent_response(
            agent=agent,
            channel="chat:test-conv",
            conversation_id="test-conv",
            turn=1
        )
        
        assert isinstance(response, Message)
        assert response.sender == "agent_0"
        assert response.turn == 1
        
        # Verify agent was called with history
        agent.generate_response.assert_called_once_with(history)
    
    @pytest.mark.asyncio
    async def test_get_agent_response_failure(self, mock_orchestrator):
        """Test agent response generation failure."""
        orchestrator, mocks = mock_orchestrator
        await orchestrator.initialize()
        
        # Make agent fail
        agent = mocks["agents"][0]
        agent.generate_response.side_effect = Exception("Agent failed")
        
        with pytest.raises(Exception, match="Agent failed"):
            await orchestrator._get_agent_response(
                agent=agent,
                channel="chat:test-conv",
                conversation_id="test-conv",
                turn=1
            )


@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integration tests for orchestrator."""
    
    @pytest.mark.skip(reason="Requires running services and API keys")
    @pytest.mark.asyncio
    async def test_full_orchestration_flow(self):
        """Test full orchestration with real services."""
        # This would test with actual Redis, PostgreSQL, and Gemini API
        pass 