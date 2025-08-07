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

# Add routes gradually as they work
try:
    from src.api.routes import auth, memory, context, relation
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    app.include_router(context.router, prefix="/api/context", tags=["context"])
    app.include_router(relation.router, prefix="/api/relation", tags=["relation"])
    logger.info("All routes loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load some routes: {e}")
    logger.info("Running in minimal mode")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)