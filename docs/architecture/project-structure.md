# Enhanced MCP Multi-Context Memory System - Project Structure

## Overview
This document outlines the project structure for the enhanced MCP Multi-Context Memory System, which combines SQLite backend with existing JSONL storage while maintaining backward compatibility.

## Directory Structure

```
mcp-multi-context-memory/
├── docs/                          # Documentation
│   ├── migration-guide.md         # Migration from JSONL to SQLite
│   ├── testing-plan.md           # Testing strategy
│   ├── deployment-plan.md        # Deployment procedures
│   ├── implementation-plan.md    # Technical implementation details
│   ├── roadmap.md               # 20-week implementation timeline
│   ├── project-plan.md          # Complete project overview
│   ├── implementation-summary.md # Summary of all documentation
│   └── project-structure.md     # This file
├── src/                          # Source code
│   ├── __init__.py              # Package initialization
│   ├── database/                # SQLite backend
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── enhanced_memory_db.py # EnhancedMemoryDB class
│   │   └── migrations/          # Database migrations
│   │       ├── __init__.py
│   │       └── upgrade_v1_to_v2.py
│   ├── api/                     # FastAPI server
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── routes/              # API routes
│   │   │   ├── __init__.py
│   │   │   ├── memory.py        # Memory operations
│   │   │   ├── config.py        # Configuration
│   │   │   └── admin.py         # Admin operations
│   │   ├── schemas/             # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── memory.py
│   │   │   └── config.py
│   │   └── dependencies.py      # Dependencies
│   ├── mcp/                     # MCP protocol handler
│   │   ├── __init__.py
│   │   ├── server.py            # MCP server implementation
│   │   └── protocol.py          # MCP protocol utilities
│   ├── migration/               # Migration tools
│   │   ├── __init__.py
│   │   ├── jsonl_to_sqlite.py   # JSONL to SQLite migration
│   │   └── validation.py        # Data validation
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py          # Settings management
│   │   └── logging.py           # Logging configuration
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── crypto.py            # Cryptographic utilities
│   │   ├── text_processing.py   # Text processing utilities
│   │   └── error_handling.py    # Error handling utilities
│   └── extension/               # VS Code extension
│       ├── __init__.py
│       ├── client.py            # Extension client
│       └── protocol.py          # Extension protocol
├── tests/                       # Test files
│   ├── __init__.py
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── test_database.py
│   │   ├── test_api.py
│   │   └── test_mcp.py
│   ├── integration/             # Integration tests
│   │   ├── __init__.py
│   │   ├── test_full_system.py
│   │   └── test_migration.py
│   └── e2e/                     # End-to-end tests
│       ├── __init__.py
│       ├── test_workflow.py
│       └── test_performance.py
├── scripts/                     # Utility scripts
│   ├── __init__.py
│   ├── migrate.py               # Migration script
│   ├── start_server.py          # Server startup script
│   └── test_runner.py           # Test runner script
├── data/                        # Data storage
│   ├── jsonl/                   # Original JSONL storage
│   │   ├── contexts.jsonl
│   │   ├── memories.jsonl
│   │   └── relations.jsonl
│   └── sqlite/                  # SQLite database
│       └── memory.db
├── config/                      # Configuration files
│   ├── settings.yaml            # Main settings
│   ├── logging.yaml             # Logging configuration
│   └── development.yaml         # Development settings
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── pyproject.toml               # Project metadata
├── .env.example                 # Environment variables example
├── .gitignore                   # Git ignore file
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
└── README.md                    # Project README
```

## Key Components

### 1. Database Backend (`src/database/`)
- **models.py**: SQLAlchemy models for entities
- **enhanced_memory_db.py**: Main database interface
- **migrations/**: Database schema migration scripts

### 2. API Server (`src/api/`)
- **main.py**: FastAPI application entry point
- **routes/**: API endpoints for memory operations
- **schemas/**: Pydantic models for request/response validation

### 3. MCP Protocol Handler (`src/mcp/`)
- **server.py**: MCP server implementation
- **protocol.py**: MCP protocol utilities

### 4. Migration Tools (`src/migration/`)
- **jsonl_to_sqlite.py**: Migration script from JSONL to SQLite
- **validation.py**: Data validation utilities

### 5. Configuration Management (`src/config/`)
- **settings.py**: Settings management
- **logging.py**: Logging configuration

### 6. VS Code Extension (`src/extension/`)
- **client.py**: Extension client implementation
- **protocol.py**: Extension protocol utilities

### 7. Testing (`tests/`)
- **unit/**: Unit tests for individual components
- **integration/**: Integration tests for component interactions
- **e2e/**: End-to-end tests for complete workflows

### 8. Data Storage (`data/`)
- **jsonl/**: Original JSONL storage (maintained for backward compatibility)
- **sqlite/**: SQLite database storage

## File Descriptions

### Core Files
- **`requirements.txt`**: Lists all Python dependencies
- **`setup.py`**: Package setup and installation script
- **`pyproject.toml`**: Project metadata and build configuration
- **`.env.example`**: Example environment variables
- **`Dockerfile`**: Docker container configuration
- **`docker-compose.yml`**: Docker Compose configuration

### Configuration Files
- **`config/settings.yaml`**: Main application settings
- **`config/logging.yaml`**: Logging configuration
- **`config/development.yaml`**: Development-specific settings

### Data Files
- **`data/jsonl/contexts.jsonl`**: Context data in JSONL format
- **`data/jsonl/memories.jsonl`**: Memory data in JSONL format
- **`data/jsonl/relations.jsonl`**: Relation data in JSONL format
- **`data/sqlite/memory.db`**: SQLite database file

### Scripts
- **`scripts/migrate.py`**: Migration script for data conversion
- **`scripts/start_server.py`**: Server startup script
- **`scripts/test_runner.py`**: Test runner script

## Implementation Notes

1. **Backward Compatibility**: The `data/jsonl/` directory is preserved to maintain compatibility with existing systems.

2. **Migration Path**: The `src/migration/` directory contains tools for migrating from JSONL to SQLite.

3. **Configuration**: The `config/` directory contains YAML files for configuration management.

4. **Testing**: The `tests/` directory is organized by test type (unit, integration, e2e).

5. **Documentation**: The `docs/` directory contains all documentation files.

6. **Data Storage**: The `data/` directory contains both JSONL and SQLite storage, with SQLite as the primary storage for the enhanced system.

This project structure supports the hybrid architecture design, allowing for a gradual migration from JSONL to SQLite while maintaining backward compatibility.