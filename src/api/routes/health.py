from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "mcp-memory"
    }

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MCP Multi-Context Memory System",
        "version": "2.0.0",
        "status": "running"
    }