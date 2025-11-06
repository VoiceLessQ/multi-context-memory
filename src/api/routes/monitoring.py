"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Monitoring routes for the MCP Multi-Context Memory System.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from ...database.refactored_memory_db import RefactoredMemoryDB
from ...monitoring.memory_monitor import MemoryMonitor
from ...monitoring.dashboard import MonitoringDashboard
from ...database.session import get_db
from ..dependencies import get_enhanced_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/metrics")
async def get_metrics(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get system metrics.
    
    Returns:
        Dictionary containing system metrics
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Get metrics
        metrics = memory_monitor.generate_report()
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.get("/alerts")
async def get_alerts(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> List[Dict[str, Any]]:
    """
    Get system alerts.
    
    Returns:
        List of system alerts
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Get alerts
        alerts = memory_monitor.get_alerts()
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.get("/memory-usage")
async def get_memory_usage(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get memory usage statistics.
    
    Returns:
        Dictionary containing memory usage statistics
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Get memory usage stats
        stats = memory_monitor.get_memory_usage_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting memory usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get memory usage stats")

@router.get("/compression-stats")
async def get_compression_stats(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get compression statistics.
    
    Returns:
        Dictionary containing compression statistics
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Get compression stats
        stats = memory_monitor.get_compression_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting compression stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compression stats")

@router.get("/lazy-loading-stats")
async def get_lazy_loading_stats(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get lazy loading statistics.
    
    Returns:
        Dictionary containing lazy loading statistics
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Get lazy loading stats
        stats = memory_monitor.get_lazy_loading_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting lazy loading stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get lazy loading stats")

@router.get("/performance-stats")
async def get_performance_stats(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get performance statistics.
    
    Returns:
        Dictionary containing performance statistics
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Get performance stats
        stats = memory_monitor.get_performance_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance stats")

@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get dashboard data.
    
    Returns:
        Dictionary containing dashboard data
    """
    try:
        # Initialize dashboard
        dashboard = MonitoringDashboard(enhanced_db.db_url, db)
        
        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data()
        
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/dashboard/html")
async def get_html_dashboard(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> str:
    """
    Get HTML dashboard.
    
    Returns:
        HTML string for dashboard display
    """
    try:
        # Initialize dashboard
        dashboard = MonitoringDashboard(enhanced_db.db_url, db)
        
        # Get HTML dashboard
        html_dashboard = dashboard.generate_html_dashboard()
        
        return html_dashboard
    
    except Exception as e:
        logger.error(f"Error getting HTML dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get HTML dashboard")

@router.get("/export-metrics")
async def export_metrics(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> str:
    """
    Export metrics in specified format.
    
    Args:
        format: Export format (json or csv)
        
    Returns:
        Metrics data in specified format
    """
    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor(enhanced_db.db_url, db)
        
        # Export metrics
        metrics = memory_monitor.export_metrics(format)
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")

@router.post("/collect-historical-data")
async def collect_historical_data(
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Collect historical data for charts.
    
    Returns:
        Dictionary with collection status
    """
    try:
        # Initialize dashboard
        dashboard = MonitoringDashboard(enhanced_db.db_url, db)
        
        # Collect historical data
        dashboard.collect_historical_data()
        
        return {
            "status": "success",
            "message": "Historical data collected successfully"
        }
    
    except Exception as e:
        logger.error(f"Error collecting historical data: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect historical data")

@router.get("/historical-data")
async def get_historical_data(
    metric: str = Query(..., pattern="^(memory_usage|compression_ratio|lazy_loading_ratio|response_time|error_rate)$"),
    points: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    enhanced_db: RefactoredMemoryDB = Depends(get_enhanced_db)
) -> Dict[str, Any]:
    """
    Get historical data for a specific metric.
    
    Args:
        metric: Metric name
        points: Number of data points to return
        
    Returns:
        Dictionary containing historical data
    """
    try:
        # Initialize dashboard
        dashboard = MonitoringDashboard(enhanced_db.db_url, db)
        
        # Get historical data
        historical_data = dashboard.historical_data.get(metric, [])
        
        # Limit data points
        if len(historical_data) > points:
            historical_data = historical_data[-points:]
        
        return {
            "metric": metric,
            "data": historical_data,
            "count": len(historical_data)
        }
    
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get historical data")