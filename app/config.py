"""Configuration management for the poly-agents system."""

import json

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class AgentModelConfig:
    """Configuration for individual agent models."""
    def __init__(self, agent_id: str, model: str, temperature: float = 0.7, personality: str | None = None):
        self.agent_id = agent_id
        self.model = model
        self.temperature = temperature
        self.personality = personality


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # Agent Settings
    num_agents: int = Field(default=3, description="Number of agents to spawn")
    default_turns: int = Field(default=2, description="Default conversation turns")
    consensus_algorithm: str = Field(default="synthesis", description="Consensus algorithm (synthesis, semantic, or majority_vote)")

    # Gemini Settings - Default fallback
    gemini_api_key: str | None = Field(default=None, description="Gemini API key")
    gemini_model: str = Field(default="gemini-pro", description="Default Gemini model name")
    gemini_temperature: float = Field(default=0.7, description="Default Gemini temperature")
    gemini_max_tokens: int = Field(default=4000, description="Gemini max tokens")

    # Multi-Model Configuration (JSON string)
    agent_models_config: str | None = Field(
        default=None,
        description="JSON configuration for agent-specific models"
    )

    # Redis Settings
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_stream_maxlen: int = Field(default=1000, description="Redis stream max length")

    # PostgreSQL Settings
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="postgres", description="PostgreSQL user")
    postgres_password: str = Field(default="password", description="PostgreSQL password")
    postgres_db: str = Field(default="polyagents", description="PostgreSQL database")
    postgres_echo: bool = Field(default=False, description="SQLAlchemy echo")

    # Qdrant Settings (Optional)
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_vector_size: int = Field(default=384, description="Vector embedding size")

    # Security Settings
    jwt_secret_key: str | None = Field(default=None, description="JWT secret key for token signing")
    api_key_enabled: bool = Field(default=True, description="Enable API key authentication")
    rate_limiting_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per window")
    rate_limit_window: int = Field(default=3600, description="Rate limit window in seconds")
    rate_limit_burst: int = Field(default=10, description="Rate limit burst allowance")

    # Default API Keys (JSON string)
    default_api_keys: str | None = Field(
        default=None,
        description="JSON configuration for default API keys"
    )

    # CORS Settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:8080"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_allow_methods: list[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="CORS allowed methods")
    cors_allow_headers: list[str] = Field(
        default=["*", "Authorization", "Content-Type", "X-Requested-With"],
        description="CORS allowed headers"
    )

    # Health Check Settings
    health_check_timeout: float = Field(default=5.0, description="Health check timeout in seconds")
    health_check_external_services: bool = Field(default=True, description="Include external service checks in health")

    # Error Handling Settings
    retry_max_attempts: int = Field(default=3, description="Maximum retry attempts for failed operations")
    retry_base_delay: float = Field(default=1.0, description="Base delay for exponential backoff")
    retry_max_delay: float = Field(default=60.0, description="Maximum delay for exponential backoff")
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_timeout: float = Field(default=60.0, description="Circuit breaker timeout in seconds")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Development
    debug: bool = Field(default=False, description="Debug mode")

    # Local LLM Model (for embedding, summary, fusion)
    local_llm_model: str = Field(default="Qwen/Qwen3-0.6B", description="Local LLM model for embedding, summary, fusion")

    @validator('agent_models_config')
    def validate_agent_models_config(cls, v):
        """Validate the JSON configuration for agent models."""
        if v is None:
            return v
        try:
            config = json.loads(v)
            if not isinstance(config, list):
                raise ValueError("agent_models_config must be a JSON list")
            for item in config:
                if not isinstance(item, dict) or 'agent_id' not in item or 'model' not in item:
                    raise ValueError("Each agent config must have 'agent_id' and 'model' fields")
            return v
        except json.JSONDecodeError:
            raise ValueError("agent_models_config must be valid JSON")

    @validator('default_api_keys')
    def validate_default_api_keys(cls, v):
        """Validate the JSON configuration for default API keys."""
        if v is None:
            return v
        try:
            config = json.loads(v)
            if not isinstance(config, list):
                raise ValueError("default_api_keys must be a JSON list")
            for item in config:
                if not isinstance(item, dict) or 'name' not in item:
                    raise ValueError("Each API key config must have 'name' field")
            return v
        except json.JSONDecodeError:
            raise ValueError("default_api_keys must be valid JSON")

    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        """Validate CORS origins."""
        if not v:
            return ["*"]
        return v

    def get_agent_configs(self) -> list[AgentModelConfig]:
        """Get parsed agent model configurations."""
        if not self.agent_models_config:
            # Default configuration: create N agents with default model
            return [
                AgentModelConfig(
                    agent_id=f"agent_{i}",
                    model=self.gemini_model,
                    temperature=self.gemini_temperature
                )
                for i in range(self.num_agents)
            ]

        # Parse custom configuration
        config_data = json.loads(self.agent_models_config)
        agent_configs = []

        for item in config_data:
            agent_config = AgentModelConfig(
                agent_id=item['agent_id'],
                model=item['model'],
                temperature=item.get('temperature', self.gemini_temperature),
                personality=item.get('personality')
            )
            agent_configs.append(agent_config)

        return agent_configs

    def get_model_for_agent(self, agent_id: str) -> str:
        """Get the model name for a specific agent."""
        agent_configs = self.get_agent_configs()
        for config in agent_configs:
            if config.agent_id == agent_id:
                return config.model
        return self.gemini_model  # fallback

    def get_temperature_for_agent(self, agent_id: str) -> float:
        """Get the temperature for a specific agent."""
        agent_configs = self.get_agent_configs()
        for config in agent_configs:
            if config.agent_id == agent_id:
                return config.temperature
        return self.gemini_temperature  # fallback

    def get_default_api_keys(self) -> list[dict]:
        """Get parsed default API keys configuration."""
        if not self.default_api_keys:
            return []

        try:
            return json.loads(self.default_api_keys)
        except json.JSONDecodeError:
            return []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
