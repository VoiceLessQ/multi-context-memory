# MCP Multi-Context Memory System - Examples

This directory contains practical examples and tutorials for using the MCP Multi-Context Memory System.

## Directory Structure

```
examples/
├── basic/              # Basic usage examples
├── advanced/           # Advanced features and patterns
├── integrations/       # Integration examples with other tools
└── README.md          # This file
```

## Getting Started

### Prerequisites

1. **MCP Server Running**: Ensure the MCP server is running locally or via Docker
   ```bash
   docker-compose up -d
   ```

2. **Python Environment**: Python 3.8+ with required dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**: Copy and configure `.env.example`
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Available Examples

### Basic Examples

1. **[01_simple_memory.py](basic/01_simple_memory.py)** - Create and retrieve a simple memory
2. **[02_search_memories.py](basic/02_search_memories.py)** - Search for memories using text and semantic search
3. **[03_contexts.py](basic/03_contexts.py)** - Organize memories using contexts
4. **[04_relationships.py](basic/04_relationships.py)** - Create relationships between memories
5. **[05_bulk_operations.py](basic/05_bulk_operations.py)** - Efficient bulk memory creation

### Advanced Examples

1. **[01_semantic_search.py](advanced/01_semantic_search.py)** - Advanced semantic search with caching
2. **[02_knowledge_graph.py](advanced/02_knowledge_graph.py)** - Build and query knowledge graphs
3. **[03_book_ingestion.py](advanced/03_book_ingestion.py)** - Ingest and index entire books
4. **[04_content_analytics.py](advanced/04_content_analytics.py)** - Analyze and categorize content
5. **[05_custom_embeddings.py](advanced/05_custom_embeddings.py)** - Use custom embedding models

### Integration Examples

1. **[kilo_code_integration.py](integrations/kilo_code_integration.py)** - Full Kilo Code integration
2. **[rest_api_client.py](integrations/rest_api_client.py)** - REST API client implementation
3. **[async_batch_processor.py](integrations/async_batch_processor.py)** - Async batch processing
4. **[mcp_tools_demo.py](integrations/mcp_tools_demo.py)** - Complete MCP tools demonstration

## Running Examples

### Option 1: Direct Python Execution

```bash
# Navigate to examples directory
cd examples

# Run a basic example
python basic/01_simple_memory.py

# Run an advanced example
python advanced/01_semantic_search.py
```

### Option 2: With Docker

```bash
# Ensure services are running
docker-compose up -d

# Run example in container
docker-compose exec api-server python /app/examples/basic/01_simple_memory.py
```

### Option 3: Interactive Jupyter Notebook

```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
jupyter notebook

# Open any .ipynb file in examples/
```

## Configuration

Most examples use these environment variables:

```bash
# API Configuration
API_HOST=localhost
API_PORT=8002
API_BASE_URL=http://localhost:8002

# Database
DATABASE_URL=sqlite:///./data/sqlite/memory.db

# Redis (for caching)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Vector Search
CHROMA_ENABLED=true
VECTOR_SEARCH_ENABLED=true

# Embeddings
EMBEDDING_PROVIDER=local  # or 'openai'
```

## Example Output

Each example includes:
- ✅ Clear comments explaining each step
- ✅ Error handling and validation
- ✅ Expected output samples
- ✅ Performance metrics where applicable

## Troubleshooting

### Connection Refused

```bash
# Check if server is running
curl http://localhost:8002/health

# Start services if not running
docker-compose up -d
```

### Import Errors

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, sqlalchemy, chromadb; print('OK')"
```

### Permission Errors

```bash
# Fix data directory permissions
chmod -R 755 data/
```

## Contributing Examples

Want to contribute an example? Great!

1. Create a new file in the appropriate directory
2. Include comprehensive comments
3. Add error handling
4. Update this README with a description
5. Test thoroughly
6. Submit a pull request

## Additional Resources

- **Full Documentation**: [../README.md](../README.md)
- **API Reference**: http://localhost:8002/docs
- **Architecture Guide**: [../ARCHITECTURE_ANALYSIS.md](../ARCHITECTURE_ANALYSIS.md)
- **Usage Guide**: [../docs/USAGE.md](../docs/USAGE.md)

---

**Copyright (c) 2024 VoiceLessQ**
**Licensed under MIT License**
