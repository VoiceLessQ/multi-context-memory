"""
FastAPI application entry point for the enhanced MCP Multi-Context Memory System.
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from contextlib import asynccontextmanager

from src.config.settings import get_settings
from src.config.logging import setup_logging
from src.database.enhanced_memory_db import EnhancedMemoryDB
from src.utils.error_handling import add_exception_handlers
from src.api.routes import auth, memory, context, relation, config, admin, monitoring
from src.api.dependencies import get_enhanced_db, get_current_user
from src.schemas.auth import TokenData
from src.config.manager import ConfigManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global database instance
db_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    """
    # Startup
    logger.info("Starting MCP Multi-Context Memory System")
    
    # Initialize configuration manager
    global config_manager
    config_manager = ConfigManager()
    
    # Initialize database
    global db_instance
    app_settings = get_settings()
    db_instance = EnhancedMemoryDB(
        db_url=app_settings.database_url,
        hybrid_storage_config={"jsonl_path": app_settings.jsonl_data_path}
    )
    
    # Initialize database
    await db_instance.initialize()
    
    # Initialize hybrid storage
    await db_instance.initialize_hybrid_storage()
    
    # Create tables if they don't exist
    await db_instance.create_tables()
    
    # Load initial data
    await db_instance.load_initial_data()
    
    # Apply configuration to database
    config = config_manager.get_config()
    
    # Set database configuration
    db_instance.set_compression_enabled(config.compression.enabled)
    db_instance.set_compression_algorithm(config.compression.algorithm)
    db_instance.set_compression_level(config.compression.level)
    db_instance.set_compression_threshold(config.compression.threshold)
    
    db_instance.set_lazy_loading_enabled(config.lazy_loading.enabled)
    db_instance.set_preview_length(config.lazy_loading.preview_length)
    db_instance.set_eager_load_threshold(config.lazy_loading.eager_load_threshold)
    
    db_instance.set_chunked_storage_enabled(config.chunked_storage.enabled)
    db_instance.set_chunk_size(config.chunked_storage.chunk_size)
    db_instance.set_max_chunks(config.chunked_storage.max_chunks)
    
    logger.info("MCP Multi-Context Memory System started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Multi-Context Memory System")
    
    # Close database connections
    if db_instance:
        await db_instance.close()
    
    logger.info("MCP Multi-Context Memory System shut down successfully")

# Create FastAPI app
app_settings = get_settings()
app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    description="Enhanced MCP Multi-Context Memory System with SQLite backend",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=app_settings.allowed_hosts
)

# Add exception handlers
add_exception_handlers(app)

# Add static files (if any)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    memory.router,
    prefix="/api/v1/memory",
    tags=["Memory"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    context.router,
    prefix="/api/v1/context",
    tags=["Context"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    relation.router,
    prefix="/api/v1/relation",
    tags=["Relation"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    config.router,
    prefix="/api/v1/config",
    tags=["Configuration"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Administration"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    monitoring.router,
    prefix="/api/v1/monitoring",
    tags=["Monitoring"],
    dependencies=[Depends(get_current_user)]
)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to MCP Multi-Context Memory System",
        "version": app_settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    try:
        # Check database connection
        if db_instance:
            await db_instance.check_connection()
            return {
                "status": "healthy",
                "database": "connected",
                "version": app_settings.app_version
            }
        else:
            return {
                "status": "degraded",
                "database": "not initialized",
                "version": app_settings.app_version
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": app_settings.app_version
        }

# Info endpoint
@app.get("/info")
async def info():
    """
    System information endpoint.
    """
    return {
        "name": app_settings.app_name,
        "version": app_settings.app_version,
        "description": "Enhanced MCP Multi-Context Memory System",
        "features": [
            "SQLite backend",
            "JSONL compatibility",
            "MCP protocol support",
            "VS Code extension",
            "AI-powered summarization",
            "Knowledge graph",
            "Full-text search",
            "Multi-level access control",
            "Data migration",
            "Backup and restore",
            "Performance monitoring",
            "Compression optimization",
            "Lazy loading",
            "Chunked storage",
            "Real-time dashboard"
        ],
        "endpoints": {
            "auth": "/api/v1/auth",
            "memory": "/api/v1/memory",
            "context": "/api/v1/context",
            "relation": "/api/v1/relation",
            "config": "/api/v1/config",
            "admin": "/api/v1/admin",
            "monitoring": "/api/v1/monitoring",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "info": "/info"
        }
    }

# MCP protocol endpoint
@app.post("/mcp")
async def mcp_handler(request: Request):
    """
    MCP protocol handler endpoint.
    """
    try:
        # Get MCP request data
        mcp_data = await request.json()
        
        # Process MCP request
        response = await process_mcp_request(mcp_data)
        
        return response
        
    except Exception as e:
        logger.error(f"MCP handler error: {e}")
        raise HTTPException(status_code=500, detail="MCP processing failed")

async def process_mcp_request(mcp_data: dict):
    """
    Process MCP request.
    
    Args:
        mcp_data: MCP request data
        
    Returns:
        MCP response
    """
    # Extract MCP request details
    method = mcp_data.get("method")
    params = mcp_data.get("params", {})
    id = mcp_data.get("id")
    
    # Process based on method
    if method == "memory.search":
        # Search memories
        query = params.get("query", "")
        filters = params.get("filters", {})
        
        memories = await db_instance.search_memories(query, filters)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "memories": [memory.dict() for memory in memories]
            },
            "id": id
        }
        
    elif method == "memory.create":
        # Create memory
        memory_data = params.get("memory", {})
        
        memory = await db_instance.create_memory(memory_data)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "memory": memory.dict()
            },
            "id": id
        }
        
    elif method == "memory.update":
        # Update memory
        memory_id = params.get("id")
        memory_data = params.get("memory", {})
        
        memory = await db_instance.update_memory(memory_id, memory_data)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "memory": memory.dict()
            },
            "id": id
        }
        
    elif method == "memory.delete":
        # Delete memory
        memory_id = params.get("id")
        
        await db_instance.delete_memory(memory_id)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "success": True
            },
            "id": id
        }
        
    elif method == "context.search":
        # Search contexts
        query = params.get("query", "")
        filters = params.get("filters", {})
        
        contexts = await db_instance.search_contexts(query, filters)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "contexts": [context.dict() for context in contexts]
            },
            "id": id
        }
        
    elif method == "context.create":
        # Create context
        context_data = params.get("context", {})
        
        context = await db_instance.create_context(context_data)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "context": context.dict()
            },
            "id": id
        }
        
    elif method == "context.update":
        # Update context
        context_id = params.get("id")
        context_data = params.get("context", {})
        
        context = await db_instance.update_context(context_id, context_data)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "context": context.dict()
            },
            "id": id
        }
        
    elif method == "context.delete":
        # Delete context
        context_id = params.get("id")
        
        await db_instance.delete_context(context_id)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "success": True
            },
            "id": id
        }
        
    elif method == "relation.search":
        # Search relations
        query = params.get("query", "")
        filters = params.get("filters", {})
        
        relations = await db_instance.search_relations(query, filters)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "relations": [relation.dict() for relation in relations]
            },
            "id": id
        }
        
    elif method == "relation.create":
        # Create relation
        relation_data = params.get("relation", {})
        
        relation = await db_instance.create_relation(relation_data)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "relation": relation.dict()
            },
            "id": id
        }
        
    elif method == "relation.update":
        # Update relation
        relation_id = params.get("id")
        relation_data = params.get("relation", {})
        
        relation = await db_instance.update_relation(relation_id, relation_data)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "relation": relation.dict()
            },
            "id": id
        }
        
    elif method == "relation.delete":
        # Delete relation
        relation_id = params.get("id")
        
        await db_instance.delete_relation(relation_id)
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "success": True
            },
            "id": id
        }
        
    else:
        # Unknown method
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": "Method not found"
            },
            "id": id
        }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """
    WebSocket endpoint for real-time updates.
    """
    await websocket.accept()
    
    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            
            # Process message
            response = await process_mcp_request(data)
            
            # Send response
            await websocket.send_text(response)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=app_settings.api_host,
        port=app_settings.api_port,
        reload=app_settings.debug,
        workers=app_settings.api_workers
    )