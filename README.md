# Poly-Agents Gemini System

A production-ready, containerized multi-agent system that runs multiple Google Gemini agents in parallel, facilitates debate through Redis Streams, reaches consensus, and returns unified answers via a FastAPI gateway.

## 🏗️ Architecture

- **Gateway**: FastAPI server exposing REST API and WebSocket endpoints
- **Orchestrator**: Coordinates multiple agents and manages conversation flow
- **Agents**: Thin wrappers around Google Gemini models with distinct personalities
- **Consensus Engine**: Pluggable algorithms for reaching agreement (majority vote with tie-breaking)
- **Memory Layer**: 
  - Redis Streams for real-time inter-agent communication
  - PostgreSQL for audit logging and conversation persistence
  - Qdrant for semantic similarity and long-term memory (optional)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key
- Python ≥3.11 (for local development)

### Using Docker Compose (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd polyagents-gemini
   cp env.example .env
   ```

2. **Configure environment**:
   Edit `.env` and set your Gemini API key:
   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Start the system**:
   ```bash
   make dev-up
   # or manually:
   docker-compose up -d
   ```

4. **Test the API**:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "What are the pros and cons of renewable energy?"}'
   ```

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start infrastructure**:
   ```bash
   docker-compose up redis postgres qdrant -d
   ```

3. **Run the API**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📡 API Endpoints

### POST /chat
Submit a prompt for multi-agent discussion and consensus.

**Request**:
```json
{
  "prompt": "What is the best approach to climate change?"
}
```

**Response**:
```json
{
  "conversation_id": "uuid-here",
  "answer": "Consensus response from all agents..."
}
```

### WebSocket /stream
Real-time conversation updates (TODO: implementation pending).

### GET /health
Health check endpoint.

## 🔧 Configuration

All configuration is managed via environment variables. See `env.example` for the complete list.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | **Required**: Your Google Gemini API key |
| `NUM_AGENTS` | 3 | Number of agents to spawn (used only if no custom config) |
| `DEFAULT_TURNS` | 2 | Default conversation turns |
| `GEMINI_MODEL` | gemini-pro | Default Gemini model (fallback) |

### Multi-Model Configuration

You can configure each agent with different models, temperatures, and personalities using the `AGENT_MODELS_CONFIG` JSON variable:

```bash
AGENT_MODELS_CONFIG='[
  {
    "agent_id": "agent_0",
    "model": "gemini-pro", 
    "temperature": 0.3,
    "personality": "You are a conservative analyst focused on facts."
  },
  {
    "agent_id": "agent_1",
    "model": "gemini-pro-vision",
    "temperature": 0.9, 
    "personality": "You are a creative visionary with innovative ideas."
  },
  {
    "agent_id": "agent_2",
    "model": "gemini-ultra",
    "temperature": 0.5,
    "personality": "You are a critical thinker who challenges assumptions."
  }
]'
```

**Available Gemini Models**:
- `gemini-pro` - Standard text model
- `gemini-pro-vision` - Multimodal model (text + images)
- `gemini-ultra` - Most capable model (when available)

**Configuration Fields**:
- `agent_id`: Unique identifier (e.g., "agent_0", "specialist_1")  
- `model`: Gemini model name
- `temperature`: Creativity level (0.0-1.0)
- `personality`: Custom personality prompt (optional)

If `AGENT_MODELS_CONFIG` is not set, the system creates `NUM_AGENTS` agents using the default `GEMINI_MODEL`.

### Infrastructure Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `POSTGRES_HOST` | localhost | PostgreSQL host |
| `POSTGRES_USER` | postgres | PostgreSQL username |
| `POSTGRES_PASSWORD` | password | PostgreSQL password |
| `QDRANT_HOST` | localhost | Qdrant host (optional) |

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest

# Unit tests only (exclude integration tests)
pytest -m "not integration"

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_gateway.py -v
```

## 🛠️ Development Tools

The project includes comprehensive tooling:

```bash
# Code formatting
black app/ tests/

# Linting
ruff check app/ tests/

# Type checking
mypy app/

# Run all quality checks
make lint
```

## 🐳 Docker Commands

Common Docker operations:

```bash
# Start all services
make dev-up

# View logs
docker-compose logs -f api

# Rebuild and restart API
docker-compose up --build -d api

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

## 🔍 How It Works

1. **User submits prompt** via POST /chat
2. **Orchestrator spawns N agents** with configured models and personalities
3. **Agents debate in parallel** for N turns (default: 2):
   - Each agent uses its specific Gemini model and temperature
   - Responses stored in Redis Streams
   - All messages logged to PostgreSQL
4. **Consensus engine** applies majority vote:
   - Vote on first line of final responses
   - Tie-breaker: longest response wins
   - Fallback: alphabetical ordering
5. **System returns unified answer** with conversation ID

### Example Multi-Model Debate

With different models configured:
- **Agent 0** (gemini-pro, temp=0.3): Provides factual, conservative analysis
- **Agent 1** (gemini-pro-vision, temp=0.9): Offers creative, innovative solutions
- **Agent 2** (gemini-ultra, temp=0.5): Delivers balanced critical assessment

This creates richer debates with diverse perspectives and reasoning styles.

## 📊 Monitoring and Observability

- **Health checks**: Built into Docker containers
- **Structured logging**: JSON logs with correlation IDs
- **Database audit trail**: All conversations and messages persisted
- **Model tracking**: Each message includes agent model information
- **Metrics**: Ready for Prometheus integration (TODO)

## 🔮 Future Enhancements

- [ ] WebSocket streaming for real-time agent debates
- [ ] Ray integration for CPU-bound consensus algorithms
- [ ] Semantic consensus using vector similarity
- [ ] Agent performance scoring and adaptive weighting
- [ ] Dynamic model selection based on conversation context
- [ ] Cross-model conversation analysis and insights
- [ ] Advanced memory retrieval using Qdrant

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and quality checks
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**"Gemini API key not found"**
- Ensure `GEMINI_API_KEY` is set in your `.env` file
- Verify the API key is valid and has proper permissions

**"Invalid JSON in AGENT_MODELS_CONFIG"**
- Check JSON syntax is valid
- Ensure each agent config has required `agent_id` and `model` fields
- Use single quotes around the JSON string in `.env`

**"Model not available"**
- Some Gemini models may not be available in all regions
- Check Google AI Studio for model availability
- Fall back to `gemini-pro` if other models fail

**"Redis connection failed"**
- Check Redis is running: `docker-compose ps redis`
- Verify network connectivity: `docker-compose logs redis`

**"PostgreSQL connection failed"**
- Ensure PostgreSQL is healthy: `docker-compose ps postgres`
- Check credentials match `.env` configuration

### Getting Help

- Check the logs: `docker-compose logs -f api`
- Verify service health: `curl http://localhost:8000/health`
- Test agent configuration: Check startup logs for model assignments 