# PolyAgents - Multi-Agent Gemini System

A sophisticated multi-agent system with consensus mechanism using Google Gemini API, featuring real-time streaming, advanced security, comprehensive health monitoring, and robust error handling.

## 🚀 Features

### Core Features
- **Multi-Agent Conversations**: Orchestrates multiple Gemini agents with different models/temperatures
- **Consensus Mechanism**: Majority vote with tie-breaking for reliable decision making
- **Real-time Streaming**: WebSocket support for live conversation updates
- **Memory Layer**: Redis Streams for inter-agent communication + PostgreSQL for persistence
- **Vector Search**: Optional Qdrant integration for semantic search capabilities

### Security & Authentication
- **API Key Authentication**: Secure access control with configurable permissions
- **Rate Limiting**: Burst-aware rate limiting with per-client tracking
- **JWT Token Support**: Stateless authentication with configurable expiration
- **Input Validation**: Comprehensive sanitization and validation
- **IP Blocking**: Automatic blocking of malicious IPs
- **CORS Configuration**: Flexible cross-origin resource sharing settings

### Monitoring & Observability
- **Advanced Health Checks**: Component-level monitoring with response times
- **System Metrics**: Real-time statistics for conversations, agents, and errors
- **Circuit Breaker Pattern**: Automatic fault tolerance for external services
- **Error Tracking**: Detailed error logging with contextual information
- **Performance Monitoring**: Response time tracking and bottleneck identification

### Resilience & Reliability
- **Retry Logic**: Exponential backoff with jitter for failed operations
- **Graceful Degradation**: Fallback responses when services are unavailable
- **Connection Pooling**: Efficient resource management for databases
- **Background Tasks**: Automatic cleanup and maintenance operations
- **Service Discovery**: Health-aware service routing and load balancing

## 📋 Requirements

- Python 3.8+
- Google Gemini API key
- Redis 6.0+
- PostgreSQL 12+
- Qdrant (optional)

## 🔧 Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd PolyAgents-main
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp env.example .env
# Edit .env with your configurations
```

### 4. Set up infrastructure

#### Using Docker Compose (Recommended)
```bash
docker-compose up -d
```

#### Manual Setup
```bash
# Redis
redis-server

# PostgreSQL
createdb polyagents

# Qdrant (optional)
docker run -p 6333:6333 qdrant/qdrant
```

### 5. Run the application
```bash
python -m app.main
```

## ⚙️ Configuration

### Environment Variables

#### Core Settings
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Agent Configuration
NUM_AGENTS=3
DEFAULT_TURNS=2

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
```

#### Security Settings
```env
# Authentication
JWT_SECRET_KEY=your_very_secure_secret_key_here
API_KEY_ENABLED=true

# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_BURST=10

# Default API Keys (JSON)
DEFAULT_API_KEYS=[
  {
    "name": "admin_user",
    "key": "pk_admin_1234567890abcdef",
    "permissions": ["read", "write", "admin"],
    "rate_limit_override": 1000
  }
]
```

#### Error Handling & Resilience
```env
# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60.0

# Health Checks
HEALTH_CHECK_TIMEOUT=5.0
HEALTH_CHECK_EXTERNAL_SERVICES=true
```

### Multi-Model Configuration

Configure different models per agent:

```env
AGENT_MODELS_CONFIG=[
  {
    "agent_id": "agent_0",
    "model": "gemini-pro",
    "temperature": 0.3,
    "personality": "analytical"
  },
  {
    "agent_id": "agent_1", 
    "model": "gemini-pro-vision",
    "temperature": 0.8,
    "personality": "creative"
  },
  {
    "agent_id": "agent_2",
    "model": "gemini-pro",
    "temperature": 0.5,
    "personality": "critical"
  }
]
```

## 🌐 API Endpoints

### Authentication
All protected endpoints require an API key in the Authorization header:
```bash
Authorization: Bearer your_api_key_here
```

### Chat Endpoints

#### POST /chat
Start a conversation with multiple agents.

**Request:**
```json
{
  "message": "What are the benefits of renewable energy?",
  "conversation_id": "optional-uuid",
  "num_agents": 3,
  "turns": 2
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "agent_responses": [
    {
      "agent_id": "agent_0",
      "response": "Renewable energy reduces carbon emissions...",
      "model": "gemini-pro",
      "temperature": 0.3
    }
  ],
  "consensus_result": "Final consensus response",
  "metadata": {
    "status": "completed",
    "duration": 2.5,
    "turns_completed": 2
  }
}
```

#### POST /stream/{conversation_id}
Start a streaming conversation.

**Response:**
```json
{
  "conversation_id": "uuid",
  "status": "started",
  "websocket_url": "/ws/uuid"
}
```

### Real-time WebSocket

#### WS /ws/{conversation_id}
Connect to real-time conversation updates.

**Messages:**
```json
{
  "type": "agent_response",
  "agent_id": "agent_0",
  "content": "Agent response...",
  "turn": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}

{
  "type": "consensus_update",
  "consensus": "Current consensus state...",
  "confidence": 0.85,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Health & Monitoring

#### GET /health
Basic health check (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "service": "polyagents"
}
```

#### GET /health/detailed
Comprehensive health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "redis": {
      "status": "healthy",
      "response_time_ms": 50.2,
      "details": {
        "memory_usage_bytes": 1048576,
        "connected_clients": 5
      }
    },
    "postgresql": {
      "status": "healthy",
      "response_time_ms": 120.5,
      "details": {
        "database_size_bytes": 52428800,
        "active_connections": 3
      }
    },
    "gemini_api": {
      "status": "healthy",
      "response_time_ms": 300.1,
      "details": {
        "available_models": 10,
        "api_key_configured": true
      }
    }
  },
  "summary": {
    "total_components": 7,
    "healthy": 6,
    "degraded": 1,
    "unhealthy": 0
  }
}
```

### Conversation Management

#### GET /conversations/recent
Get recent conversations.

**Query Parameters:**
- `limit`: Number of conversations (default: 10)

#### GET /conversations/{conversation_id}
Get conversation details and messages.

#### POST /conversations/search
Search conversations by content.

**Request:**
```json
{
  "query": "renewable energy",
  "limit": 10
}
```

### Statistics & Analytics

#### GET /statistics
Get comprehensive system statistics.

**Response:**
```json
{
  "conversations": {
    "total_conversations": 1250,
    "conversations_today": 45,
    "average_duration": 3.2,
    "success_rate": 0.96
  },
  "agents": {
    "total_messages": 8750,
    "average_response_time": 1.8,
    "model_distribution": {
      "gemini-pro": 0.7,
      "gemini-pro-vision": 0.3
    }
  },
  "errors": {
    "chat_conversation": {
      "total_24h": 12,
      "rate_1h": 0.5
    }
  },
  "circuit_breakers": {
    "gemini_api": {
      "state": "closed",
      "failure_count": 0,
      "last_failure_time": null
    }
  }
}
```

### Administration

#### POST /admin/cleanup
Clean up old data (requires admin permission).

**Query Parameters:**
- `days`: Retention period (default: 30)

**Response:**
```json
{
  "cleanup_results": {
    "postgresql": {
      "conversations": 25,
      "messages": 150
    },
    "redis": {
      "deleted_streams": 8
    }
  },
  "days_threshold": 30
}
```

#### GET /admin/export
Export conversation data (requires admin permission).

**Query Parameters:**
- `format`: Export format (json)
- `days`: Export period (default: 7)

## 🔒 Security Features

### API Key Management
- Configurable permissions: `read`, `write`, `admin`
- Per-key rate limiting overrides
- Automatic key rotation support
- Secure key generation utilities

### Rate Limiting
- Token bucket algorithm with burst capacity
- Per-client tracking with Redis backend
- Configurable limits per endpoint
- IP-based blocking for abuse prevention

### Input Validation
- Comprehensive sanitization of all inputs
- SQL injection prevention
- XSS protection
- File upload security (when applicable)

### Monitoring & Alerting
- Real-time security event logging
- Failed authentication tracking
- Rate limit violation alerts
- Suspicious activity detection

## 🏥 Health Monitoring

### Component Health Checks
- **Redis**: Connection, memory usage, client count
- **PostgreSQL**: Connection, database size, active queries
- **Qdrant**: Collection status, vector count
- **Gemini API**: Model availability, quota status
- **System Resources**: Memory, disk space, CPU usage

### Health Status Levels
- **Healthy**: All systems operational
- **Degraded**: Minor issues, partial functionality
- **Unhealthy**: Critical issues, service impacted
- **Unknown**: Unable to determine status

### Automatic Recovery
- Circuit breakers for external services
- Graceful degradation with fallback responses
- Automatic retry with exponential backoff
- Health-based load balancing

## 🔄 Error Handling & Resilience

### Retry Logic
- Exponential backoff with jitter
- Configurable retry attempts and delays
- Smart exception classification
- Retry statistics and monitoring

### Circuit Breaker Pattern
- Automatic failure detection
- Configurable failure thresholds
- Half-open state for recovery testing
- Service-specific breaker instances

### Graceful Degradation
- Cached response fallbacks
- Minimal functionality modes
- User-friendly error messages
- Service availability indicators

## 📊 Monitoring & Analytics

### Key Metrics
- **Response Time**: P50, P95, P99 percentiles
- **Error Rate**: Errors per hour, success rate
- **Throughput**: Requests per second
- **Resource Usage**: Memory, CPU, connections

### Error Tracking
- Error classification and trending
- Stack trace collection
- Performance impact analysis
- Automated alerting thresholds

### Performance Optimization
- Database query optimization
- Connection pool tuning
- Cache hit rate monitoring
- Resource bottleneck identification

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-specific Overrides
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  app:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RATE_LIMITING_ENABLED=false
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests
pytest tests/test_gateway.py::TestAuthentication

# Integration tests
pytest tests/test_orchestrator.py::TestIntegration

# Security tests
pytest tests/test_security.py
```

### Test Coverage
```bash
pytest --cov=app --cov-report=html
```

## 🔧 Development

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

### Code Quality
```bash
# Linting
flake8 app/
black app/
isort app/

# Type checking
mypy app/
```

### Performance Profiling
```bash
# Memory profiling
python -m memory_profiler app/main.py

# Performance profiling
python -m cProfile -o profile.stats app/main.py
```

## 📈 Performance Tuning

### Database Optimization
- Connection pooling configuration
- Query optimization and indexing
- Read replicas for analytics
- Automated vacuum and statistics

### Redis Optimization
- Memory usage optimization
- Persistence configuration
- Clustering for high availability
- Stream compaction policies

### Application Optimization
- Async/await best practices
- Connection reuse patterns
- Caching strategies
- Resource pool management

## 🚨 Troubleshooting

### Common Issues

#### High Response Times
1. Check database connection pool
2. Monitor Redis memory usage
3. Verify Gemini API quotas
4. Review error logs for patterns

#### Authentication Failures
1. Verify API key configuration
2. Check rate limiting status
3. Review CORS settings
4. Validate JWT secret key

#### WebSocket Connection Issues
1. Check Redis connectivity
2. Verify firewall settings
3. Monitor connection limits
4. Review proxy configuration

### Debugging Tools
```bash
# Health check debugging
curl -X GET "http://localhost:8000/health/detailed"

# Redis inspection
redis-cli monitor

# PostgreSQL query analysis
EXPLAIN ANALYZE <query>

# Application logs
tail -f logs/polyagents.log
```

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For issues and questions:
1. Check the troubleshooting guide
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and configuration details

---

**Note**: This is a development version. For production deployment, ensure proper security configurations, monitoring setup, and resource provisioning. 