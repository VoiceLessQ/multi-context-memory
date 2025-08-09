from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="MCP Memory System",
    version="2.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "name": "MCP Memory System",
        "version": "2.0.0",
        "status": "running"
    }

# Add routes individually with better error handling
loaded_routes = []

# Try to load memory routes first (most important)
try:
    from src.api.routes import memory
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    loaded_routes.append("memory")
    logger.info("Memory routes loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load memory routes: {e}")

# Try to load auth routes
try:
    from src.api.routes import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    loaded_routes.append("auth")
    logger.info("Auth routes loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load auth routes: {e}")

# Try to load context routes
try:
    from src.api.routes import context
    app.include_router(context.router, prefix="/api/context", tags=["context"])
    loaded_routes.append("context")
    logger.info("Context routes loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load context routes: {e}")

# Try to load relation routes
try:
    from src.api.routes import relation
    app.include_router(relation.router, prefix="/api/relation", tags=["relation"])
    loaded_routes.append("relation")
    logger.info("Relation routes loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load relation routes: {e}")

if loaded_routes:
    logger.info(f"Successfully loaded routes: {', '.join(loaded_routes)}")
else:
    logger.warning("No routes loaded - running in minimal mode")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)