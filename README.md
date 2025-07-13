# PolyAgents - Multi-Agent Gemini System

A sophisticated multi-agent system with consensus mechanism using Google Gemini API, featuring real-time streaming, advanced security, comprehensive health monitoring, and robust error handling.

## 🚀 Features

### Core Features
- **Multi-Agent Conversations**: Orchestrates multiple Gemini agents with different models/temperatures
- **Intelligent Consensus Mechanism**: LLM-powered synthesis that combines the best insights from all agents
- **Real-time Streaming**: WebSocket support for live conversation updates
- **Memory Layer**: Redis Streams for inter-agent communication + PostgreSQL for persistence
- **Vector Search**: Optional Qdrant integration for semantic search capabilities
- **Complete Agent Responses**: Full-length responses with expandable modal views
- **Progress Tracking**: Real-time status updates during agent processing

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

### 2. Configure environment
```bash
cp env.example .env
# Edit .env with your configurations
```

### 3. Run with Docker Compose (Recommended)

#### Development Mode (Recommended for development and testing)
```bash
# Build and start development environment with hot reloading
docker-compose -f docker-compose.dev.yml up -d --build

# Access the application
# Frontend: http://localhost:8080 (with hot reloading)
# Backend API: http://localhost:8000
# WebSocket: ws://localhost:8000/ws
```

#### Full Stack (Frontend + Backend)
```bash
# Build and start all services
docker-compose up -d --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:3000/api
# WebSocket: ws://localhost:3000/ws
```

#### Backend Only
```bash
# Start only backend services
docker-compose up -d api redis postgres qdrant

# Access the API directly
# API: http://localhost:8000
# WebSocket: ws://localhost:8000/ws
```

### 4. Manual Setup (Development)

#### Backend Dependencies
```bash
pip install -r requirements.txt
```

#### Frontend Dependencies
```bash
cd frontend
npm install
```

#### Infrastructure Setup
```bash
# Redis
redis-server

# PostgreSQL
createdb polyagents

# Qdrant (optional)
docker run -p 6333:6333 qdrant/qdrant
```

#### Run Services
```bash
# Backend
python -m app.main

# Frontend (in another terminal)
cd frontend
npm run dev
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
CONSENSUS_ALGORITHM=synthesis

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=4000
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

## 🎨 Frontend

The PolyAgents frontend is a modern React application built with:

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Shadcn/ui** for UI components
- **React Query** for state management
- **WebSocket** for real-time updates

### Frontend Features

- **Real-time Chat Interface**: Live conversation with multiple agents
- **Agent Status Panel**: Monitor agent activity and system health
- **Conversation Management**: Browse, search, and manage conversations
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Modern dark theme optimized for long sessions
- **WebSocket Integration**: Real-time updates for agent responses and status
- **Expandable Agent Responses**: Click to view complete agent responses in modal
- **Progress Tracking**: Real-time status updates during processing

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Frontend Configuration

The frontend uses environment variables for configuration:

```env
# Production environment (frontend/env.production)
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost/ws
VITE_API_KEY=pa_your_secret_key_here
```

### Frontend Architecture

- **Components**: Modular UI components in `src/components/`
- **Pages**: Route components in `src/pages/`
- **Services**: API and WebSocket services in `src/services/`
- **Hooks**: Custom React hooks in `src/hooks/`
- **Types**: TypeScript definitions in `src/types/`

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
  "agents": {
    "count": 3,
    "turns": 2,
    "temperature": 0.7,
    "model": "gemini-pro"
  }
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "message_id": "msg-uuid",
  "response": "Final consensus response",
  "agent_responses": [
    {
      "agent_id": "agent_0",
      "content": "Analytical perspective on renewable energy...",
      "status": "ready"
    },
    {
      "agent_id": "agent_1", 
      "content": "Creative insights on renewable energy...",
      "status": "ready"
    },
    {
      "agent_id": "agent_2",
      "content": "Critical analysis of renewable energy...",
      "status": "ready"
    }
  ],
  "consensus": {
    "content": "Synthesized response combining all perspectives...",
    "explanation": "Consensus reached using synthesis algorithm"
  },
  "metadata": {
    "status": "success",
    "turns": 2,
    "num_agents": 3
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

### Development (Recommended)
```bash
docker-compose -f docker-compose.dev.yml up -d --build
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

---

---

# PolyAgents - Sistema Multi-Agente Gemini

Un sistema multi-agente sofisticato con meccanismo di consenso utilizzando l'API Google Gemini, con streaming in tempo reale, sicurezza avanzata, monitoraggio completo della salute e gestione robusta degli errori.

## 🚀 Funzionalità

### Funzionalità Core
- **Conversazioni Multi-Agente**: Orchestrazione di più agenti Gemini con modelli/temperature diversi
- **Meccanismo di Consenso Intelligente**: Sintesi basata su LLM che combina i migliori insight di tutti gli agenti
- **Streaming in Tempo Reale**: Supporto WebSocket per aggiornamenti live delle conversazioni
- **Livello di Memoria**: Redis Streams per comunicazione inter-agente + PostgreSQL per persistenza
- **Ricerca Vettoriale**: Integrazione opzionale Qdrant per capacità di ricerca semantica
- **Risposte Complete degli Agenti**: Risposte a lunghezza completa con viste modali espandibili
- **Tracciamento del Progresso**: Aggiornamenti di stato in tempo reale durante l'elaborazione degli agenti

### Sicurezza e Autenticazione
- **Autenticazione API Key**: Controllo accessi sicuro con permessi configurabili
- **Rate Limiting**: Rate limiting con burst capacity e tracciamento per client
- **Supporto JWT Token**: Autenticazione stateless con scadenza configurabile
- **Validazione Input**: Sanitizzazione e validazione completa
- **Blocco IP**: Blocco automatico di IP malevoli
- **Configurazione CORS**: Impostazioni flessibili per condivisione risorse cross-origin

### Monitoraggio e Osservabilità
- **Health Check Avanzati**: Monitoraggio a livello di componente con tempi di risposta
- **Metriche di Sistema**: Statistiche in tempo reale per conversazioni, agenti ed errori
- **Pattern Circuit Breaker**: Tolleranza automatica ai guasti per servizi esterni
- **Tracciamento Errori**: Logging dettagliato degli errori con informazioni contestuali
- **Monitoraggio Performance**: Tracciamento tempi di risposta e identificazione colli di bottiglia

### Resilienza e Affidabilità
- **Logica di Retry**: Backoff esponenziale con jitter per operazioni fallite
- **Degradazione Graceful**: Risposte di fallback quando i servizi non sono disponibili
- **Connection Pooling**: Gestione efficiente delle risorse per i database
- **Task in Background**: Operazioni automatiche di pulizia e manutenzione
- **Service Discovery**: Routing e bilanciamento del carico basati sulla salute

## 📋 Requisiti

- Python 3.8+
- Chiave API Google Gemini
- Redis 6.0+
- PostgreSQL 12+
- Qdrant (opzionale)

## 🔧 Installazione

### 1. Clona il repository
```bash
git clone <repository-url>
cd PolyAgents-main
```

### 2. Configura l'ambiente
```bash
cp env.example .env
# Modifica .env con le tue configurazioni
```

### 3. Esegui con Docker Compose (Raccomandato)

#### Modalità Sviluppo (Raccomandato per sviluppo e test)
```bash
# Build e avvia l'ambiente di sviluppo con hot reloading
docker-compose -f docker-compose.dev.yml up -d --build

# Accedi all'applicazione
# Frontend: http://localhost:8080 (con hot reloading)
# Backend API: http://localhost:8000
# WebSocket: ws://localhost:8000/ws
```

#### Stack Completo (Frontend + Backend)
```bash
# Build e avvia tutti i servizi
docker-compose up -d --build

# Accedi all'applicazione
# Frontend: http://localhost:3000
# Backend API: http://localhost:3000/api
# WebSocket: ws://localhost:3000/ws
```

#### Solo Backend
```bash
# Avvia solo i servizi backend
docker-compose up -d api redis postgres qdrant

# Accedi direttamente all'API
# API: http://localhost:8000
# WebSocket: ws://localhost:8000/ws
```

### 4. Setup Manuale (Sviluppo)

#### Dipendenze Backend
```bash
pip install -r requirements.txt
```

#### Dipendenze Frontend
```bash
cd frontend
npm install
```

#### Setup Infrastruttura
```bash
# Redis
redis-server

# PostgreSQL
createdb polyagents

# Qdrant (opzionale)
docker run -p 6333:6333 qdrant/qdrant
```

#### Esegui Servizi
```bash
# Backend
python -m app.main

# Frontend (in un altro terminale)
cd frontend
npm run dev
```

## ⚙️ Configurazione

### Variabili d'Ambiente

#### Impostazioni Core
```env
# Configurazione API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Configurazione Agenti
NUM_AGENTS=3
DEFAULT_TURNS=2
CONSENSUS_ALGORITHM=synthesis

# API Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=4000
```

#### Impostazioni Sicurezza
```env
# Autenticazione
JWT_SECRET_KEY=your_very_secure_secret_key_here
API_KEY_ENABLED=true

# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_BURST=10

# API Keys di Default (JSON)
DEFAULT_API_KEYS=[
  {
    "name": "admin_user",
    "key": "pk_admin_1234567890abcdef",
    "permissions": ["read", "write", "admin"],
    "rate_limit_override": 1000
  }
]
```

#### Gestione Errori e Resilienza
```env
# Configurazione Retry
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

### Configurazione Multi-Modello

Configura modelli diversi per agente:

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

## 🎨 Frontend

Il frontend PolyAgents è un'applicazione React moderna costruita con:

- **React 18** con TypeScript
- **Vite** per sviluppo veloce e building
- **Tailwind CSS** per lo styling
- **Shadcn/ui** per i componenti UI
- **React Query** per la gestione dello stato
- **WebSocket** per aggiornamenti in tempo reale

### Funzionalità Frontend

- **Interfaccia Chat in Tempo Reale**: Conversazione live con più agenti
- **Pannello Stato Agenti**: Monitora attività degli agenti e salute del sistema
- **Gestione Conversazioni**: Sfoglia, cerca e gestisci conversazioni
- **Design Responsive**: Funziona su desktop e dispositivi mobili
- **Modalità Scura**: Tema scuro moderno ottimizzato per sessioni lunghe
- **Integrazione WebSocket**: Aggiornamenti in tempo reale per risposte e stato degli agenti
- **Risposte Agenti Espandibili**: Clicca per vedere risposte complete degli agenti in modal
- **Tracciamento Progresso**: Aggiornamenti di stato in tempo reale durante l'elaborazione

### Sviluppo Frontend

```bash
# Installa dipendenze
cd frontend
npm install

# Avvia server di sviluppo
npm run dev

# Build per produzione
npm run build

# Anteprima build produzione
npm run preview
```

### Configurazione Frontend

Il frontend usa variabili d'ambiente per la configurazione:

```env
# Ambiente produzione (frontend/env.production)
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost/ws
VITE_API_KEY=pa_your_secret_key_here
```

### Architettura Frontend

- **Components**: Componenti UI modulari in `src/components/`
- **Pages**: Componenti di routing in `src/pages/`
- **Services**: Servizi API e WebSocket in `src/services/`
- **Hooks**: Custom React hooks in `src/hooks/`
- **Types**: Definizioni TypeScript in `src/types/`

## 🌐 Endpoint API

### Autenticazione
Tutti gli endpoint protetti richiedono una API key nell'header Authorization:
```bash
Authorization: Bearer your_api_key_here
```

### Endpoint Chat

#### POST /chat
Avvia una conversazione con più agenti.

**Request:**
```json
{
  "message": "Quali sono i benefici dell'energia rinnovabile?",
  "conversation_id": "optional-uuid",
  "agents": {
    "count": 3,
    "turns": 2,
    "temperature": 0.7,
    "model": "gemini-pro"
  }
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "message_id": "msg-uuid",
  "response": "Risposta consenso finale",
  "agent_responses": [
    {
      "agent_id": "agent_0",
      "content": "Prospettiva analitica sull'energia rinnovabile...",
      "status": "ready"
    },
    {
      "agent_id": "agent_1", 
      "content": "Insight creativi sull'energia rinnovabile...",
      "status": "ready"
    },
    {
      "agent_id": "agent_2",
      "content": "Analisi critica dell'energia rinnovabile...",
      "status": "ready"
    }
  ],
  "consensus": {
    "content": "Risposta sintetizzata che combina tutte le prospettive...",
    "explanation": "Consenso raggiunto usando algoritmo di sintesi"
  },
  "metadata": {
    "status": "success",
    "turns": 2,
    "num_agents": 3
  }
}
```

#### POST /stream/{conversation_id}
Avvia una conversazione in streaming.

**Response:**
```json
{
  "conversation_id": "uuid",
  "status": "started",
  "websocket_url": "/ws/uuid"
}
```

### WebSocket in Tempo Reale

#### WS /ws/{conversation_id}
Connetti per aggiornamenti conversazione in tempo reale.

**Messaggi:**
```json
{
  "type": "agent_response",
  "agent_id": "agent_0",
  "content": "Risposta agente...",
  "turn": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}

{
  "type": "consensus_update",
  "consensus": "Stato consenso corrente...",
  "confidence": 0.85,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Salute e Monitoraggio

#### GET /health
Health check base (non richiede autenticazione).

**Response:**
```json
{
  "status": "healthy",
  "service": "polyagents"
}
```

#### GET /health/detailed
Health check completo con stato componenti.

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

### Gestione Conversazioni

#### GET /conversations/recent
Ottieni conversazioni recenti.

**Query Parameters:**
- `limit`: Numero conversazioni (default: 10)

#### GET /conversations/{conversation_id}
Ottieni dettagli conversazione e messaggi.

#### POST /conversations/search
Cerca conversazioni per contenuto.

**Request:**
```json
{
  "query": "energia rinnovabile",
  "limit": 10
}
```

### Statistiche e Analytics

#### GET /statistics
Ottieni statistiche complete del sistema.

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

### Amministrazione

#### POST /admin/cleanup
Pulisci dati vecchi (richiede permesso admin).

**Query Parameters:**
- `days`: Periodo di retention (default: 30)

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
Esporta dati conversazione (richiede permesso admin).

**Query Parameters:**
- `format`: Formato esportazione (json)
- `days`: Periodo esportazione (default: 7)

## 🔒 Funzionalità Sicurezza

### Gestione API Key
- Permessi configurabili: `read`, `write`, `admin`
- Override rate limiting per chiave
- Supporto rotazione automatica chiavi
- Utility generazione chiavi sicure

### Rate Limiting
- Algoritmo token bucket con capacità burst
- Tracciamento per client con backend Redis
- Limiti configurabili per endpoint
- Blocco basato su IP per prevenzione abusi

### Validazione Input
- Sanitizzazione completa di tutti gli input
- Prevenzione SQL injection
- Protezione XSS
- Sicurezza upload file (quando applicabile)

### Monitoraggio e Alerting
- Logging eventi sicurezza in tempo reale
- Tracciamento autenticazioni fallite
- Alert violazioni rate limit
- Rilevamento attività sospette

## 🏥 Monitoraggio Salute

### Health Check Componenti
- **Redis**: Connessione, uso memoria, numero client
- **PostgreSQL**: Connessione, dimensione database, query attive
- **Qdrant**: Stato collezione, numero vettori
- **Gemini API**: Disponibilità modelli, stato quota
- **Risorse Sistema**: Memoria, spazio disco, uso CPU

### Livelli Stato Salute
- **Healthy**: Tutti i sistemi operativi
- **Degraded**: Problemi minori, funzionalità parziale
- **Unhealthy**: Problemi critici, servizio impattato
- **Unknown**: Impossibile determinare stato

### Recupero Automatico
- Circuit breakers per servizi esterni
- Degradazione graceful con risposte fallback
- Retry automatico con backoff esponenziale
- Bilanciamento carico basato su salute

## 🔄 Gestione Errori e Resilienza

### Logica Retry
- Backoff esponenziale con jitter
- Tentativi retry e ritardi configurabili
- Classificazione intelligente eccezioni
- Statistiche retry e monitoraggio

### Pattern Circuit Breaker
- Rilevamento automatico fallimenti
- Soglie fallimento configurabili
- Stato half-open per test recupero
- Istanze breaker specifiche per servizio

### Degradazione Graceful
- Risposte fallback in cache
- Modalità funzionalità minima
- Messaggi errore user-friendly
- Indicatori disponibilità servizio

## 📊 Monitoraggio e Analytics

### Metriche Chiave
- **Tempo Risposta**: Percentili P50, P95, P99
- **Tasso Errore**: Errori per ora, tasso successo
- **Throughput**: Richieste per secondo
- **Uso Risorse**: Memoria, CPU, connessioni

### Tracciamento Errori
- Classificazione errori e trend
- Raccolta stack trace
- Analisi impatto performance
- Soglie alerting automatizzate

### Ottimizzazione Performance
- Ottimizzazione query database
- Tuning connection pool
- Monitoraggio cache hit rate
- Identificazione colli di bottiglia risorse

## 🐳 Deploy Docker

### Sviluppo (Raccomandato)
```bash
docker-compose -f docker-compose.dev.yml up -d --build
```


### Override Specifici per Ambiente
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

### Esegui Tutti i Test
```bash
pytest
```

### Esegui Categorie Test Specifiche
```bash
# Test unitari
pytest tests/test_gateway.py::TestAuthentication

# Test integrazione
pytest tests/test_orchestrator.py::TestIntegration

# Test sicurezza
pytest tests/test_security.py
```

### Coverage Test
```bash
pytest --cov=app --cov-report=html
```

## 🔧 Sviluppo

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

### Qualità Codice
```bash
# Linting
flake8 app/
black app/
isort app/

# Type checking
mypy app/
```

### Profiling Performance
```bash
# Memory profiling
python -m memory_profiler app/main.py

# Performance profiling
python -m cProfile -o profile.stats app/main.py
```

## 📈 Ottimizzazione Performance

### Ottimizzazione Database
- Configurazione connection pooling
- Ottimizzazione query e indici
- Replica read per analytics
- Automated vacuum and statistics

### Ottimizzazione Redis
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

## 📚 Documentazione API

La documentazione API interattiva è disponibile su:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch feature
3. Implementa modifiche con test
4. Aggiorna documentazione
5. Invia pull request

## 📄 Licenza

Questo progetto è licenziato sotto MIT License - vedi il file [LICENSE](LICENSE) per dettagli.

## 🙋‍♂️ Supporto

Per problemi e domande:
1. Controlla la guida troubleshooting
2. Rivedi issue GitHub esistenti
3. Crea una nuova issue con informazioni dettagliate
4. Includi log e dettagli configurazione

---

**Nota**: Questa è una versione di sviluppo. Per deploy produzione, assicurati di configurazioni sicurezza appropriate, setup monitoraggio e provisioning risorse. 