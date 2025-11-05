"""
Settings management for the enhanced MCP Multi-Context Memory System.
Provides centralized configuration with environment variable support.
"""
import os
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="MCP Multi-Context Memory", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # Database
    database_url: str = Field(default="sqlite:///./data/sqlite/memory.db", env="DATABASE_URL")
    jsonl_data_path: str = Field(default="./data/jsonl/", env="JSONL_DATA_PATH")
    
    # API Server
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    
    # Security
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # MCP Server
    mcp_host: str = Field(default="localhost", env="MCP_HOST")
    mcp_port: int = Field(default=5000, env="MCP_PORT")
    
    # VS Code Extension
    extension_host: str = Field(default="localhost", env="EXTENSION_HOST")
    extension_port: int = Field(default=3000, env="EXTENSION_PORT")
    
    # Embedding Model
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_provider: str = Field(default="local", env="EMBEDDING_PROVIDER")  # "local" or "openai"
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_embedding_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")  # 384 for MiniLM, 1536 for OpenAI

    # Chroma Vector Database
    chroma_enabled: bool = Field(default=True, env="CHROMA_ENABLED")
    chroma_persist_directory: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY")
    chroma_collection_name: str = Field(default="knowledge_base", env="CHROMA_COLLECTION_NAME")

    # Redis Configuration
    redis_enabled: bool = Field(default=True, env="REDIS_ENABLED")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_cache_ttl: int = Field(default=3600, env="REDIS_CACHE_TTL")  # 1 hour
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")

    # Search Settings
    search_limit: int = Field(default=10, env="SEARCH_LIMIT")
    search_similarity_threshold: float = Field(default=0.5, env="SEARCH_SIMILARITY_THRESHOLD")
    vector_search_enabled: bool = Field(default=True, env="VECTOR_SEARCH_ENABLED")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/app.log", env="LOG_FILE")
    
    # CORS Settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Data Migration
    migration_enabled: bool = Field(default=True, env="MIGRATION_ENABLED")
    migration_batch_size: int = Field(default=1000, env="MIGRATION_BATCH_SIZE")
    
    # Cache Settings
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Performance Settings
    query_timeout: int = Field(default=30, env="QUERY_TIMEOUT")
    max_connections: int = Field(default=10, env="MAX_CONNECTIONS")
    
    # Development Settings
    testing: bool = Field(default=False, env="TESTING")
    
    # Allowed Hosts
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "url": self.database_url,
            "echo": self.debug,
            "pool_size": self.max_connections,
            "pool_timeout": self.query_timeout
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration."""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "workers": self.api_workers,
            "reload": self.api_reload,
            "debug": self.debug
        }
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP server configuration."""
        return {
            "host": self.mcp_host,
            "port": self.mcp_port
        }
    
    def get_extension_config(self) -> Dict[str, Any]:
        """Get VS Code extension configuration."""
        return {
            "host": self.extension_host,
            "port": self.extension_port
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.log_level,
            "file": self.log_file,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return {
            "enabled": self.cache_enabled,
            "ttl": self.cache_ttl
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "enabled": self.rate_limit_enabled,
            "requests": self.rate_limit_requests,
            "window": self.rate_limit_window
        }

    def get_chroma_config(self) -> Dict[str, Any]:
        """Get Chroma vector database configuration."""
        return {
            "enabled": self.chroma_enabled,
            "persist_directory": self.chroma_persist_directory,
            "collection_name": self.chroma_collection_name
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {
            "enabled": self.redis_enabled,
            "host": self.redis_host,
            "port": self.redis_port,
            "db": self.redis_db,
            "password": self.redis_password,
            "cache_ttl": self.redis_cache_ttl,
            "max_connections": self.redis_max_connections
        }

    def get_embedding_config(self) -> Dict[str, Any]:
        """Get embedding configuration."""
        return {
            "provider": self.embedding_provider,
            "model": self.embedding_model,
            "openai_api_key": self.openai_api_key,
            "openai_model": self.openai_embedding_model,
            "dimension": self.embedding_dimension
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

def get_settings_dict() -> Dict[str, Any]:
    """Get settings as dictionary."""
    settings = get_settings()
    return settings.dict()

def update_settings(**kwargs) -> Settings:
    """Update settings and return new instance."""
    settings = get_settings()
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings