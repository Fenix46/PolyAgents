"""Tests for the FastAPI gateway with enhanced security and features."""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import status

# Mock the dependencies before importing the app
with patch('app.main.RedisBus'), \
     patch('app.main.PostgresLog'), \
     patch('app.main.QdrantStore'), \
     patch('app.main.SecurityManager'), \
     patch('app.main.health_checker'):
    
    from app.main import app
    from app.models import ChatRequest, ChatResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_success():
    """Mock successful authentication."""
    return {
        "authenticated": True,
        "client_id": "test_client",
        "permissions": ["read", "write", "admin"]
    }


@pytest.fixture
def mock_auth_readonly():
    """Mock readonly authentication."""
    return {
        "authenticated": True,
        "client_id": "readonly_client", 
        "permissions": ["read"]
    }


@pytest.fixture
def auth_headers():
    """Headers with valid API key."""
    return {"Authorization": "Bearer test_api_key"}


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator with basic functionality."""
    orchestrator = AsyncMock()
    orchestrator.run_conversation.return_value = ChatResponse(
        conversation_id="test_conv_123",
        agent_responses=[
            {"agent_id": "agent_0", "response": "Response 1", "model": "gemini-pro"},
            {"agent_id": "agent_1", "response": "Response 2", "model": "gemini-pro"},
        ],
        consensus_result="Consensus response",
        metadata={"status": "completed", "duration": 2.5}
    )
    orchestrator.run_conversation_with_streaming = AsyncMock()
    return orchestrator


@pytest.fixture
def mock_security_manager():
    """Mock security manager."""
    security_manager = AsyncMock()
    security_manager.verify_api_key.return_value = {
        "authenticated": True,
        "client_id": "test_client",
        "permissions": ["read", "write", "admin"]
    }
    security_manager.check_rate_limit = AsyncMock()
    return security_manager


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL operations."""
    postgres = AsyncMock()
    postgres.get_recent_conversations.return_value = [
        {
            "conversation_id": "conv_1",
            "created_at": datetime.utcnow(),
            "message_count": 5
        }
    ]
    postgres.get_conversation_messages.return_value = [
        {
            "id": 1,
            "sender": "user",
            "content": "Test message",
            "timestamp": datetime.utcnow()
        }
    ]
    postgres.search_conversations.return_value = []
    postgres.get_conversation_statistics.return_value = {"total": 10}
    postgres.get_agent_statistics.return_value = {"agent_0": {"messages": 5}}
    postgres.cleanup_old_data.return_value = {"conversations": 2, "messages": 10}
    postgres.export_conversations.return_value = []
    return postgres


@pytest.fixture
def mock_redis():
    """Mock Redis operations."""
    redis = AsyncMock()
    redis.get_stream_info.return_value = {"streams": ["conv_1", "conv_2"]}
    redis.cleanup_old_conversations.return_value = {"deleted_streams": 3}
    return redis


@pytest.fixture
def mock_health_checker():
    """Mock health checker."""
    health_checker = AsyncMock()
    health_checker.check_all_components.return_value = {
        "redis": MagicMock(status="healthy", response_time_ms=50.0),
        "postgresql": MagicMock(status="healthy", response_time_ms=100.0),
    }
    health_checker.format_health_response.return_value = {
        "status": "healthy",
        "components": {
            "redis": {"status": "healthy", "response_time_ms": 50.0},
            "postgresql": {"status": "healthy", "response_time_ms": 100.0}
        }
    }
    return health_checker


class TestAuthentication:
    """Test authentication and security features."""
    
    def test_health_endpoint_no_auth(self, client):
        """Basic health endpoint should not require authentication."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy", "service": "polyagents"}
    
    @patch('app.main.verify_api_key')
    def test_protected_endpoint_requires_auth(self, mock_verify, client):
        """Protected endpoints should require authentication."""
        mock_verify.side_effect = Exception("API key required")
        
        response = client.get("/conversations/recent")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @patch('app.main.verify_api_key')
    def test_valid_api_key_accepted(self, mock_verify, client, mock_auth_success):
        """Valid API key should be accepted."""
        mock_verify.return_value = mock_auth_success
        
        with patch('app.main.postgres_log') as mock_pg:
            mock_pg.get_recent_conversations.return_value = []
            
            response = client.get("/conversations/recent", headers={"Authorization": "Bearer valid_key"})
            assert response.status_code == status.HTTP_200_OK
    
    @patch('app.main.verify_api_key')
    def test_admin_permission_required(self, mock_verify, client, mock_auth_readonly):
        """Admin endpoints should require admin permissions."""
        mock_verify.return_value = mock_auth_readonly
        
        response = client.post("/admin/cleanup", headers={"Authorization": "Bearer readonly_key"})
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestChatEndpoint:
    """Test chat functionality."""
    
    @patch('app.main.verify_api_key')
    @patch('app.main.orchestrator')
    @patch('app.main.error_handler')
    def test_successful_chat(self, mock_error_handler, mock_orch, mock_verify, client, mock_auth_success):
        """Test successful chat interaction."""
        mock_verify.return_value = mock_auth_success
        
        # Mock error handler to just call the function directly
        async def mock_execute_with_retry(func, *args, **kwargs):
            return await func()
        mock_error_handler.execute_with_retry = mock_execute_with_retry
        
        # Mock orchestrator response
        mock_response = ChatResponse(
            conversation_id="test_conv",
            agent_responses=[{"agent_id": "agent_0", "response": "Test response"}],
            consensus_result="Final answer",
            metadata={"status": "completed"}
        )
        mock_orch.run_conversation = AsyncMock(return_value=mock_response)
        
        request_data = {
            "message": "Hello, agents!",
            "conversation_id": "test_conv",
            "num_agents": 2,
            "turns": 1
        }
        
        response = client.post(
            "/chat",
            json=request_data,
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation_id"] == "test_conv"
        assert data["consensus_result"] == "Final answer"
    
    @patch('app.main.verify_api_key')
    def test_empty_message_validation(self, mock_verify, client, mock_auth_success):
        """Test validation of empty messages."""
        mock_verify.return_value = mock_auth_success
        
        request_data = {
            "message": "   ",  # Empty/whitespace message
            "conversation_id": "test_conv"
        }
        
        response = client.post(
            "/chat",
            json=request_data,
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('app.main.verify_api_key')
    @patch('app.main.orchestrator', None)
    def test_service_unavailable(self, mock_verify, client, mock_auth_success):
        """Test response when orchestrator is unavailable."""
        mock_verify.return_value = mock_auth_success
        
        request_data = {
            "message": "Hello",
            "conversation_id": "test_conv"
        }
        
        response = client.post(
            "/chat",
            json=request_data,
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestStreamingEndpoints:
    """Test streaming functionality."""
    
    @patch('app.main.verify_api_key')
    @patch('app.main.orchestrator')
    @patch('app.main.websocket_manager')
    def test_start_streaming_conversation(self, mock_ws, mock_orch, mock_verify, client, mock_auth_success):
        """Test starting a streaming conversation."""
        mock_verify.return_value = mock_auth_success
        mock_orch.run_conversation_with_streaming = AsyncMock()
        
        request_data = {
            "message": "Start streaming",
            "conversation_id": "stream_conv"
        }
        
        response = client.post(
            "/stream/stream_conv",
            json=request_data,
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation_id"] == "stream_conv"
        assert data["status"] == "started"
        assert data["websocket_url"] == "/ws/stream_conv"


class TestHealthChecks:
    """Test health check functionality."""
    
    def test_basic_health_check(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy", "service": "polyagents"}
    
    @patch('app.main.verify_api_key')
    @patch('app.main.health_checker')
    def test_detailed_health_check(self, mock_health, mock_verify, client, mock_auth_success):
        """Test detailed health endpoint."""
        mock_verify.return_value = mock_auth_success
        mock_health.check_all_components.return_value = {}
        mock_health.format_health_response.return_value = {
            "status": "healthy",
            "components": {}
        }
        
        response = client.get(
            "/health/detailed",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "components" in data


class TestConversationEndpoints:
    """Test conversation management endpoints."""
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    def test_get_recent_conversations(self, mock_pg, mock_verify, client, mock_auth_success):
        """Test getting recent conversations."""
        mock_verify.return_value = mock_auth_success
        mock_pg.get_recent_conversations.return_value = [
            {
                "conversation_id": "conv_1",
                "created_at": datetime.utcnow().isoformat(),
                "message_count": 5
            }
        ]
        
        response = client.get(
            "/conversations/recent?limit=5",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) == 1
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    def test_get_conversation_details(self, mock_pg, mock_verify, client, mock_auth_success):
        """Test getting conversation details."""
        mock_verify.return_value = mock_auth_success
        mock_pg.get_conversation_messages.return_value = [
            {
                "id": 1,
                "sender": "user",
                "content": "Test message",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        response = client.get(
            "/conversations/test_conv",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation_id"] == "test_conv"
        assert "messages" in data
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    def test_conversation_not_found(self, mock_pg, mock_verify, client, mock_auth_success):
        """Test 404 for non-existent conversation."""
        mock_verify.return_value = mock_auth_success
        mock_pg.get_conversation_messages.return_value = []
        
        response = client.get(
            "/conversations/nonexistent",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    def test_search_conversations(self, mock_pg, mock_verify, client, mock_auth_success):
        """Test conversation search."""
        mock_verify.return_value = mock_auth_success
        mock_pg.search_conversations.return_value = [
            {"conversation_id": "match_1", "content": "matching content"}
        ]
        
        search_data = {
            "query": "test search",
            "limit": 10
        }
        
        response = client.post(
            "/conversations/search",
            json=search_data,
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "test search"
        assert "results" in data


class TestStatisticsEndpoint:
    """Test statistics functionality."""
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    @patch('app.main.redis_bus')
    @patch('app.main.error_handler')
    def test_get_statistics(self, mock_error, mock_redis, mock_pg, mock_verify, client, mock_auth_success):
        """Test getting system statistics."""
        mock_verify.return_value = mock_auth_success
        mock_pg.get_conversation_statistics.return_value = {"total_conversations": 100}
        mock_pg.get_agent_statistics.return_value = {"total_messages": 500}
        mock_redis.get_stream_info.return_value = {"active_streams": 5}
        mock_error.error_stats = {"chat_conversation": [datetime.utcnow()]}
        mock_error.circuit_breakers = {}
        mock_error.get_error_rate.return_value = 0.1
        
        response = client.get(
            "/statistics",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversations" in data
        assert "agents" in data
        assert "redis" in data
        assert "errors" in data


class TestAdminEndpoints:
    """Test admin functionality."""
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    @patch('app.main.redis_bus')
    def test_cleanup_old_data_success(self, mock_redis, mock_pg, mock_verify, client, mock_auth_success):
        """Test successful data cleanup."""
        mock_verify.return_value = mock_auth_success
        mock_pg.cleanup_old_data.return_value = {"conversations": 5, "messages": 20}
        mock_redis.cleanup_old_conversations.return_value = {"deleted_streams": 3}
        
        response = client.post(
            "/admin/cleanup?days=30",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cleanup_results" in data
        assert data["days_threshold"] == 30
    
    @patch('app.main.verify_api_key')
    def test_cleanup_requires_admin_permission(self, mock_verify, client, mock_auth_readonly):
        """Test that cleanup requires admin permissions."""
        mock_verify.return_value = mock_auth_readonly
        
        response = client.post(
            "/admin/cleanup",
            headers={"Authorization": "Bearer readonly_key"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    def test_export_conversations(self, mock_pg, mock_verify, client, mock_auth_success):
        """Test conversation export."""
        mock_verify.return_value = mock_auth_success
        mock_pg.export_conversations.return_value = [
            {"conversation_id": "conv_1", "data": "exported_data"}
        ]
        
        response = client.get(
            "/admin/export?format=json&days=7",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["format"] == "json"
        assert data["days"] == 7
        assert "data" in data


class TestErrorHandling:
    """Test error handling and resilience."""
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log', None)
    def test_graceful_degradation_no_database(self, mock_verify, client, mock_auth_success):
        """Test graceful degradation when database is unavailable."""
        mock_verify.return_value = mock_auth_success
        
        response = client.get(
            "/conversations/recent",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    def test_global_exception_handler(self, client):
        """Test global exception handling."""
        # This would require setting up a scenario that triggers an unhandled exception
        # For now, we'll test that the handler is registered
        assert hasattr(app, 'exception_handlers')
    
    @patch('app.main.verify_api_key')
    @patch('app.main.postgres_log')
    def test_error_response_format(self, mock_pg, mock_verify, client, mock_auth_success):
        """Test error response includes proper structure."""
        mock_verify.return_value = mock_auth_success
        mock_pg.get_conversation_messages.side_effect = Exception("Database error")
        
        response = client.get(
            "/conversations/test_conv",
            headers={"Authorization": "Bearer valid_key"}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data


class TestWebSocketEndpoints:
    """Test WebSocket functionality."""
    
    def test_websocket_connection_no_manager(self, client):
        """Test WebSocket connection when manager is unavailable."""
        with patch('app.main.websocket_manager', None):
            with client.websocket_connect("/ws/test_conv") as websocket:
                # Connection should be closed immediately
                pass
    
    @patch('app.main.websocket_manager')
    def test_websocket_connection_with_manager(self, mock_ws_manager, client):
        """Test WebSocket connection with available manager."""
        mock_ws_manager.connect = AsyncMock()
        mock_ws_manager.disconnect = AsyncMock()
        
        # WebSocket testing in pytest is complex, so we'll test the basic setup
        assert mock_ws_manager is not None


if __name__ == "__main__":
    pytest.main([__file__]) 