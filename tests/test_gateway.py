"""Tests for the FastAPI gateway."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import Message, ConsensusResult


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing."""
    with patch("app.main.orchestrator") as mock:
        mock.initialize = AsyncMock()
        mock.cleanup = AsyncMock()
        mock.run_conversation = AsyncMock(return_value="Test consensus answer")
        yield mock


class TestChatEndpoint:
    """Tests for the /chat endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_success(self, async_client: AsyncClient, mock_orchestrator):
        """Test successful chat request."""
        # Mock the orchestrator response
        mock_orchestrator.run_conversation.return_value = "This is a test response"
        
        response = await async_client.post(
            "/chat",
            json={"prompt": "What is the weather like?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "conversation_id" in data
        assert data["answer"] == "This is a test response"
        assert len(data["conversation_id"]) > 0
        
        # Verify orchestrator was called
        mock_orchestrator.run_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_invalid_request(self, async_client: AsyncClient):
        """Test chat with invalid request body."""
        response = await async_client.post(
            "/chat",
            json={"invalid_field": "test"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_chat_empty_prompt(self, async_client: AsyncClient):
        """Test chat with empty prompt."""
        response = await async_client.post(
            "/chat",
            json={"prompt": ""}
        )
        
        assert response.status_code == 200  # Empty prompts are technically valid
    
    @pytest.mark.asyncio
    async def test_chat_orchestrator_error(self, async_client: AsyncClient, mock_orchestrator):
        """Test chat when orchestrator raises an error."""
        mock_orchestrator.run_conversation.side_effect = Exception("Orchestrator failed")
        
        response = await async_client.post(
            "/chat",
            json={"prompt": "Test prompt"}
        )
        
        assert response.status_code == 500
        assert "Orchestrator failed" in response.json()["detail"]


class TestWebSocketEndpoint:
    """Tests for the WebSocket endpoint."""
    
    @pytest.mark.asyncio
    async def test_websocket_placeholder(self, async_client: AsyncClient):
        """Test WebSocket endpoint (currently a placeholder)."""
        with async_client.websocket_connect("/stream") as websocket:
            data = websocket.receive_text()
            assert "not yet implemented" in data


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestStartupShutdown:
    """Tests for application startup and shutdown events."""
    
    @pytest.mark.asyncio
    async def test_startup_event(self, mock_orchestrator):
        """Test startup event initializes orchestrator."""
        from app.main import startup_event
        
        await startup_event()
        mock_orchestrator.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_event(self, mock_orchestrator):
        """Test shutdown event cleans up orchestrator."""
        from app.main import shutdown_event
        
        await shutdown_event()
        mock_orchestrator.cleanup.assert_called_once()


@pytest.mark.integration
class TestIntegration:
    """Integration tests (require running services)."""
    
    @pytest.mark.skip(reason="Requires running Redis/PostgreSQL services")
    @pytest.mark.asyncio
    async def test_full_chat_flow(self, async_client: AsyncClient):
        """Test full chat flow with real services."""
        # This test would require actual Redis/PostgreSQL instances
        # and a valid Gemini API key for true integration testing
        pass 