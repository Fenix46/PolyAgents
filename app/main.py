"""Main FastAPI application with enhanced security, health checks, and error handling."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import ChatRequest, ChatResponse, ConversationListResponse, MessageSearchRequest
from .orchestrator import Orchestrator
from .memory.redis_bus import RedisBus
from .memory.postgres_log import PostgresLog
from .memory.qdrant_store import QdrantStore
from .websocket import WebSocketConnectionManager
from .config import settings
from .security import SecurityManager, Permission
from .health import health_checker
from .error_handling import (
    error_handler, PolyAgentsError, AuthenticationError, ValidationError,
    RateLimitError, handle_known_exceptions, GracefulDegradation
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
redis_bus: Optional[RedisBus] = None
postgres_log: Optional[PostgresLog] = None
qdrant_store: Optional[QdrantStore] = None
orchestrator: Optional[Orchestrator] = None
websocket_manager: Optional[WebSocketConnectionManager] = None
security_manager: Optional[SecurityManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global redis_bus, postgres_log, qdrant_store, orchestrator, websocket_manager, security_manager
    
    logger.info("Starting PolyAgents application...")
    
    try:
        # Initialize security manager
        security_manager = SecurityManager()
        await security_manager.initialize()
        logger.info("Security manager initialized")
        
        # Initialize memory systems
        redis_bus = RedisBus()
        await redis_bus.initialize()
        logger.info("Redis bus initialized")
        
        postgres_log = PostgresLog()
        await postgres_log.initialize()
        logger.info("PostgreSQL log initialized")
        
        # Initialize optional Qdrant (graceful degradation if not available)
        try:
            qdrant_store = QdrantStore()
            await qdrant_store.initialize()
            logger.info("Qdrant store initialized")
        except Exception as e:
            logger.warning(f"Qdrant not available, continuing without vector search: {e}")
            qdrant_store = None
        
        # Initialize orchestrator
        orchestrator = Orchestrator(redis_bus, postgres_log, qdrant_store)
        logger.info("Orchestrator initialized")
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketConnectionManager(redis_bus)
        await websocket_manager.initialize()
        logger.info("WebSocket manager initialized")
        
        # Start background tasks
        asyncio.create_task(security_manager.start_background_tasks())
        
        logger.info("PolyAgents application started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    finally:
        logger.info("Shutting down PolyAgents application...")
        
        # Cleanup in reverse order
        if websocket_manager:
            await websocket_manager.cleanup()
        
        if redis_bus:
            await redis_bus.cleanup()
        
        if postgres_log:
            await postgres_log.cleanup()
        
        if qdrant_store:
            await qdrant_store.cleanup()
        
        if security_manager:
            await security_manager.cleanup()
        
        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="PolyAgents - Multi-Agent Gemini System",
    description="Secure multi-agent system with consensus mechanism using Google Gemini API",
    version="2.0.0",
    lifespan=lifespan
)

# Security scheme
security_scheme = HTTPBearer(auto_error=False)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*"]  # Configure for production
    )


# Security dependency
async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Dict[str, Any]:
    """Verify API key and check rate limits."""
    if not security_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security manager not initialized"
        )
    
    try:
        # Check if API key authentication is enabled
        if not settings.api_key_enabled:
            return {"authenticated": False, "permissions": [Permission.READ.value, Permission.WRITE.value]}
        
        if not credentials:
            raise AuthenticationError("API key required")
        
        # Verify API key
        api_key_info = await security_manager.verify_api_key(credentials.credentials)
        
        # Check rate limits
        client_id = api_key_info.get("client_id", "anonymous")
        await security_manager.check_rate_limit(client_id, request.client.host if request.client else "unknown")
        
        return api_key_info
        
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except Exception as e:
        logger.error(f"Security verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Security verification failed")


# Global exception handler
@app.exception_handler(PolyAgentsError)
async def polyagents_exception_handler(request: Request, exc: PolyAgentsError):
    """Handle PolyAgents custom exceptions."""
    error_type = type(exc).__name__
    
    if isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, RateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "message": str(exc),
            "timestamp": error_handler.error_stats.get("global", [])[-1].isoformat() if "global" in error_handler.error_stats else None
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    error_handler.log_error("global_exception", exc, {"path": str(request.url)})
    
    if settings.debug:
        import traceback
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


# API Endpoints

@app.post("/chat", response_model=ChatResponse)
@handle_known_exceptions("chat")
async def chat_endpoint(
    request: ChatRequest,
    auth: Dict[str, Any] = Depends(verify_api_key)
) -> ChatResponse:
    """Process a chat request with multiple agents and consensus."""
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not available"
        )
    
    try:
        # Validate input
        if not request.message.strip():
            raise ValidationError("Message cannot be empty")
        
        # Use retry logic for the chat operation
        async def run_chat():
            return await orchestrator.run_conversation(
                message=request.message,
                conversation_id=request.conversation_id,
                num_agents=request.num_agents or settings.num_agents,
                turns=request.turns or settings.default_turns
            )
        
        response = await error_handler.execute_with_retry(
            run_chat,
            "chat_conversation",
            circuit_breaker_name="gemini_api"
        )
        
        return response
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        
        # Graceful degradation - return minimal response
        return ChatResponse(
            conversation_id=request.conversation_id or "error",
            agent_responses=[],
            consensus_result="Service temporarily unavailable",
            metadata={
                "status": "error",
                "message": "Chat service is temporarily unavailable",
                "error_type": type(e).__name__
            }
        )


@app.post("/stream/{conversation_id}")
async def start_streaming_conversation(
    conversation_id: str,
    request: ChatRequest,
    auth: Dict[str, Any] = Depends(verify_api_key)
):
    """Start a streaming conversation and return connection info."""
    if not orchestrator or not websocket_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streaming service not available"
        )
    
    try:
        # Start conversation in background
        async def run_streaming_chat():
            await orchestrator.run_conversation_with_streaming(
                message=request.message,
                conversation_id=conversation_id,
                num_agents=request.num_agents or settings.num_agents,
                turns=request.turns or settings.default_turns
            )
        
        asyncio.create_task(run_streaming_chat())
        
        return {
            "conversation_id": conversation_id,
            "status": "started",
            "websocket_url": f"/ws/{conversation_id}"
        }
        
    except Exception as e:
        logger.error(f"Streaming conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start streaming conversation"
        )


@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time conversation updates."""
    if not websocket_manager:
        await websocket.close(code=1013)
        return
    
    await websocket.accept()
    
    try:
        # Add connection to manager
        await websocket_manager.connect(websocket, conversation_id)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong for keep-alive
                if message == "ping":
                    await websocket.send_text("pong")
                
            except asyncio.TimeoutError:
                # Send ping to check if connection is alive
                await websocket.send_text("ping")
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket, conversation_id)


@app.get("/health")
async def basic_health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "polyagents"}


@app.get("/health/detailed")
async def detailed_health_check(auth: Dict[str, Any] = Depends(verify_api_key)):
    """Detailed health check with component status."""
    try:
        component_healths = await health_checker.check_all_components(use_cache=True)
        return health_checker.format_health_response(component_healths)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "error"
        }


@app.get("/conversations/recent")
async def get_recent_conversations(
    limit: int = 10,
    auth: Dict[str, Any] = Depends(verify_api_key)
) -> ConversationListResponse:
    """Get recent conversations."""
    if not postgres_log:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    
    try:
        conversations = await postgres_log.get_recent_conversations(limit)
        return ConversationListResponse(conversations=conversations)
        
    except Exception as e:
        logger.error(f"Get recent conversations error: {e}")
        # Graceful degradation
        return ConversationListResponse(
            conversations=[],
            metadata=GracefulDegradation.fallback_response("conversation_list")
        )


@app.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    auth: Dict[str, Any] = Depends(verify_api_key)
):
    """Get conversation details."""
    if not postgres_log:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    
    try:
        messages = await postgres_log.get_conversation_messages(conversation_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": conversation_id,
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@app.post("/conversations/search")
async def search_conversations(
    request: MessageSearchRequest,
    auth: Dict[str, Any] = Depends(verify_api_key)
):
    """Search conversations by query."""
    if not postgres_log:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    
    try:
        results = await postgres_log.search_conversations(
            query=request.query,
            limit=request.limit or 10
        )
        return {"results": results, "query": request.query}
        
    except Exception as e:
        logger.error(f"Search conversations error: {e}")
        return {
            "results": [],
            "query": request.query,
            "error": "Search temporarily unavailable"
        }


@app.get("/statistics")
async def get_statistics(auth: Dict[str, Any] = Depends(verify_api_key)):
    """Get system statistics."""
    try:
        stats = {}
        
        if postgres_log:
            try:
                stats["conversations"] = await postgres_log.get_conversation_statistics()
                stats["agents"] = await postgres_log.get_agent_statistics()
            except Exception as e:
                logger.warning(f"Failed to get database statistics: {e}")
                stats["database"] = "unavailable"
        
        if redis_bus:
            try:
                stats["redis"] = await redis_bus.get_stream_info()
            except Exception as e:
                logger.warning(f"Failed to get Redis statistics: {e}")
                stats["redis"] = "unavailable"
        
        # Add error statistics
        stats["errors"] = {}
        for operation, timestamps in error_handler.error_stats.items():
            stats["errors"][operation] = {
                "total_24h": len(timestamps),
                "rate_1h": error_handler.get_error_rate(operation, 1)
            }
        
        # Add circuit breaker status
        stats["circuit_breakers"] = {}
        for name, breaker in error_handler.circuit_breakers.items():
            stats["circuit_breakers"][name] = breaker.get_status()
        
        return stats
        
    except Exception as e:
        logger.error(f"Statistics endpoint error: {e}")
        return GracefulDegradation.minimal_response("statistics", {"error": str(e)})


@app.get("/redis/info")
async def get_redis_info(auth: Dict[str, Any] = Depends(verify_api_key)):
    """Get Redis stream information."""
    if not redis_bus:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service not available"
        )
    
    try:
        return await redis_bus.get_stream_info()
    except Exception as e:
        logger.error(f"Redis info error: {e}")
        return GracefulDegradation.fallback_response("redis_info")


@app.post("/admin/cleanup")
async def cleanup_old_data(
    days: int = 30,
    auth: Dict[str, Any] = Depends(verify_api_key)
):
    """Cleanup old data from all storage systems."""
    # Check admin permissions
    if Permission.ADMIN.value not in auth.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    cleanup_results = {}
    
    try:
        if postgres_log:
            pg_result = await postgres_log.cleanup_old_data(days)
            cleanup_results["postgresql"] = pg_result
    except Exception as e:
        cleanup_results["postgresql"] = {"error": str(e)}
    
    try:
        if redis_bus:
            redis_result = await redis_bus.cleanup_old_conversations(days)
            cleanup_results["redis"] = redis_result
    except Exception as e:
        cleanup_results["redis"] = {"error": str(e)}
    
    try:
        if qdrant_store:
            # Qdrant cleanup would go here when implemented
            cleanup_results["qdrant"] = {"status": "not_implemented"}
    except Exception as e:
        cleanup_results["qdrant"] = {"error": str(e)}
    
    return {
        "cleanup_results": cleanup_results,
        "days_threshold": days
    }


@app.get("/admin/export")
async def export_conversations(
    format: str = "json",
    days: int = 7,
    auth: Dict[str, Any] = Depends(verify_api_key)
):
    """Export conversation data."""
    # Check admin permissions
    if Permission.ADMIN.value not in auth.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    if not postgres_log:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not available"
        )
    
    try:
        if format.lower() == "json":
            data = await postgres_log.export_conversations(days, "json")
            return {"format": "json", "data": data, "days": days}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON format is currently supported"
            )
            
    except Exception as e:
        logger.error(f"Export conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export conversations"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    ) 