"""Configuration management for the poly-agents system."""

import json
from typing import Optional, Dict, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class AgentModelConfig:
    """Configuration for individual agent models."""
    def __init__(self, agent_id: str, model: str, temperature: float = 0.7, personality: Optional[str] = None):
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
    
    # Gemini Settings - Default fallback
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    gemini_model: str = Field(default="gemini-pro", description="Default Gemini model name")
    gemini_temperature: float = Field(default=0.7, description="Default Gemini temperature")
    gemini_max_tokens: int = Field(default=1000, description="Gemini max tokens")
    
    # Multi-Model Configuration (JSON string)
    agent_models_config: Optional[str] = Field(
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
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Development
    debug: bool = Field(default=False, description="Debug mode")
    
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
    
    def get_agent_configs(self) -> List[AgentModelConfig]:
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings() 