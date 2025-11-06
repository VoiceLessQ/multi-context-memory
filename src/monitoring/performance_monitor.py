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
Performance monitoring system for the MCP Multi-Context Memory System.
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import time
import threading
import logging
from pathlib import Path
import json
import psutil
import sqlite3
from sqlalchemy.orm import Session
from collections import deque
import statistics

from ..database.models import Memory, Context, Relation

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor system performance and collect metrics."""
    
    def __init__(self, db: Session, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.config = config or {}
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 data points
        self.alerts = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.metrics_dir = Path("./data/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance thresholds
        self.thresholds = {
            "high_memory_usage": 90.0,  # Percentage
            "high_cpu_usage": 80.0,     # Percentage
            "slow_query_time": 1.0,     # Seconds
            "high_disk_usage": 90.0,    # Percentage
            "low_free_memory": 100,     # MB
        }
        
        # Alert handlers
        self.alert_handlers = []
        
        # Performance counters
        self.counters = {
            "queries_executed": 0,
            "slow_queries": 0,
            "memories_created": 0,
            "memories_updated": 0,
            "memories_deleted": 0,
            "searches_performed": 0,
            "errors_occurred": 0
        }
        
        # Query performance tracking
        self.query_times = deque(maxlen=100)
        
        # Initialize database for metrics storage
        self._init_metrics_db()
    
    def _init_metrics_db(self):
        """Initialize metrics database."""
        try:
            metrics_db_path = self.metrics_dir / "metrics.db"
            conn = sqlite3.connect(metrics_db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_timestamp TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Metrics database initialized")
        
        except Exception as e:
            logger.error(f"Error initializing metrics database: {e}")
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"Performance monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                
                # Store metrics
                self.store_metrics(metrics)
                
                # Check for alerts
                self.check_alerts(metrics)
                
                # Update counters
                self.update_counters()
                
                # Sleep for interval
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": self._collect_system_metrics(),
                "database": self._collect_database_metrics(),
                "application": self._collect_application_metrics(),
                "performance": self._collect_performance_metrics()
            }
            
            # Add to history
            self.metrics_history.append(metrics)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                "memory_total_bytes": memory.total,
                "memory_available_bytes": memory.available,
                "memory_used_bytes": memory.used,
                "memory_usage_percent": memory.percent,
                "process_memory_bytes": process.memory_info().rss,
                "process_memory_percent": process.memory_percent(),
                "cpu_usage_percent": cpu_percent,
                "cpu_count": cpu_count,
                "disk_total_bytes": disk_usage.total,
                "disk_used_bytes": disk_usage.used,
                "disk_free_bytes": disk_usage.free,
                "disk_usage_percent": disk_usage.percent,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "network_packets_sent": network.packets_sent,
                "network_packets_recv": network.packets_recv
            }
        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database-specific metrics."""
        try:
            # Database size
            db_path = Path(self.db.bind.url.database)
            db_size = db_path.stat().st_size if db_path.exists() else 0
            
            # Record counts
            memory_count = self.db.query(Memory).count()
            context_count = self.db.query(Context).count()
            relation_count = self.db.query(Relation).count()
            
            # Query performance
            avg_query_time = statistics.mean(self.query_times) if self.query_times else 0
            
            return {
                "database_size_bytes": db_size,
                "memory_count": memory_count,
                "context_count": context_count,
                "relation_count": relation_count,
                "average_query_time": avg_query_time,
                "slow_query_count": self.counters["slow_queries"],
                "total_queries": self.counters["queries_executed"]
            }
        
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}
    
    def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-level metrics."""
        try:
            return {
                "memories_created": self.counters["memories_created"],
                "memories_updated": self.counters["memories_updated"],
                "memories_deleted": self.counters["memories_deleted"],
                "searches_performed": self.counters["searches_performed"],
                "errors_occurred": self.counters["errors_occurred"],
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {}
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance-related metrics."""
        try:
            # Calculate rates
            current_time = time.time()
            
            # Query rate (queries per second)
            query_rate = self.counters["queries_executed"] / max(current_time - psutil.boot_time(), 1)
            
            # Memory growth rate
            if len(self.metrics_history) > 10:
                recent_metrics = list(self.metrics_history)[-10:]
                memory_values = [m.get("system", {}).get("process_memory_bytes", 0) for m in recent_metrics]
                if len(memory_values) > 1:
                    memory_growth = (memory_values[-1] - memory_values[0]) / len(memory_values)
                else:
                    memory_growth = 0
            else:
                memory_growth = 0
            
            return {
                "query_rate_per_second": query_rate,
                "memory_growth_rate_bytes": memory_growth,
                "cache_hit_rate": self._calculate_cache_hit_rate(),
                "compression_ratio": self._calculate_compression_ratio()
            }
        
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {}
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        try:
            # This would need to be implemented based on your caching strategy
            # For now, return a placeholder
            return 0.8  # 80% hit rate
        except Exception as e:
            logger.error(f"Error calculating cache hit rate: {e}")
            return 0.0
    
    def _calculate_compression_ratio(self) -> float:
        """Calculate compression ratio."""
        try:
            # This would need to be implemented based on your compression strategy
            # For now, return a placeholder
            return 0.6  # 60% compression ratio
        except Exception as e:
            logger.error(f"Error calculating compression ratio: {e}")
            return 0.0
    
    def store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics to database."""
        try:
            metrics_db_path = self.metrics_dir / "metrics.db"
            conn = sqlite3.connect(metrics_db_path)
            cursor = conn.cursor()
            
            # Store system metrics
            system_metrics = metrics.get("system", {})
            for key, value in system_metrics.items():
                cursor.execute('''
                    INSERT INTO performance_metrics 
                    (timestamp, metric_type, metric_name, value, unit)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    metrics["timestamp"],
                    "system",
                    key,
                    float(value) if value is not None else 0,
                    self._get_metric_unit(key)
                ))
            
            # Store database metrics
            db_metrics = metrics.get("database", {})
            for key, value in db_metrics.items():
                cursor.execute('''
                    INSERT INTO performance_metrics 
                    (timestamp, metric_type, metric_name, value, unit)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    metrics["timestamp"],
                    "database",
                    key,
                    float(value) if value is not None else 0,
                    self._get_metric_unit(key)
                ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get the unit for a metric."""
        units = {
            "memory_total_bytes": "bytes",
            "memory_available_bytes": "bytes",
            "memory_used_bytes": "bytes",
            "memory_usage_percent": "percent",
            "process_memory_bytes": "bytes",
            "process_memory_percent": "percent",
            "cpu_usage_percent": "percent",
            "cpu_count": "count",
            "disk_total_bytes": "bytes",
            "disk_used_bytes": "bytes",
            "disk_free_bytes": "bytes",
            "disk_usage_percent": "percent",
            "network_bytes_sent": "bytes",
            "network_bytes_recv": "bytes",
            "network_packets_sent": "count",
            "network_packets_recv": "count",
            "database_size_bytes": "bytes",
            "memory_count": "count",
            "context_count": "count",
            "relation_count": "count",
            "average_query_time": "seconds",
            "slow_query_count": "count",
            "total_queries": "count",
            "memories_created": "count",
            "memories_updated": "count",
            "memories_deleted": "count",
            "searches_performed": "count",
            "errors_occurred": "count",
            "uptime_seconds": "seconds",
            "query_rate_per_second": "per_second",
            "memory_growth_rate_bytes": "bytes_per_second",
            "cache_hit_rate": "percent",
            "compression_ratio": "ratio"
        }
        
        return units.get(metric_name, "unknown")
    
    def check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts."""
        try:
            alerts = []
            
            # Check system metrics
            system_metrics = metrics.get("system", {})
            
            # High memory usage
            if system_metrics.get("memory_usage_percent", 0) > self.thresholds["high_memory_usage"]:
                alerts.append({
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": f"High memory usage: {system_metrics['memory_usage_percent']:.1f}%",
                    "details": system_metrics
                })
            
            # High CPU usage
            if system_metrics.get("cpu_usage_percent", 0) > self.thresholds["high_cpu_usage"]:
                alerts.append({
                    "type": "high_cpu_usage",
                    "severity": "warning",
                    "message": f"High CPU usage: {system_metrics['cpu_usage_percent']:.1f}%",
                    "details": system_metrics
                })
            
            # High disk usage
            if system_metrics.get("disk_usage_percent", 0) > self.thresholds["high_disk_usage"]:
                alerts.append({
                    "type": "high_disk_usage",
                    "severity": "critical",
                    "message": f"High disk usage: {system_metrics['disk_usage_percent']:.1f}%",
                    "details": system_metrics
                })
            
            # Low free memory
            if system_metrics.get("memory_available_bytes", 0) < self.thresholds["low_free_memory"] * 1024 * 1024:
                alerts.append({
                    "type": "low_free_memory",
                    "severity": "warning",
                    "message": f"Low free memory: {system_metrics['memory_available_bytes'] / (1024*1024):.1f}MB",
                    "details": system_metrics
                })
            
            # Check database metrics
            db_metrics = metrics.get("database", {})
            
            # Slow queries
            if db_metrics.get("average_query_time", 0) > self.thresholds["slow_query_time"]:
                alerts.append({
                    "type": "slow_queries",
                    "severity": "warning",
                    "message": f"Slow queries detected: {db_metrics['average_query_time']:.2f}s average",
                    "details": db_metrics
                })
            
            # Process alerts
            for alert in alerts:
                self._trigger_alert(alert)
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger an alert."""
        try:
            # Store alert
            self.alerts.append(alert)
            
            # Store in database
            metrics_db_path = self.metrics_dir / "metrics.db"
            conn = sqlite3.connect(metrics_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_alerts 
                (timestamp, alert_type, severity, message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.utcnow().isoformat(),
                alert["type"],
                alert["severity"],
                alert["message"],
                json.dumps(alert.get("details", {}))
            ))
            
            conn.commit()
            conn.close()
            
            # Call alert handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
            
            logger.warning(f"Performance alert: {alert['message']}")
        
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    def add_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    def update_counters(self):
        """Update performance counters."""
        try:
            # Reset counters periodically
            current_time = time.time()
            if not hasattr(self, 'last_counter_reset'):
                self.last_counter_reset = current_time
            
            # Reset every hour
            if current_time - self.last_counter_reset > 3600:
                self.counters = {
                    "queries_executed": 0,
                    "slow_queries": 0,
                    "memories_created": 0,
                    "memories_updated": 0,
                    "memories_deleted": 0,
                    "searches_performed": 0,
                    "errors_occurred": 0
                }
                self.query_times.clear()
                self.last_counter_reset = current_time
        
        except Exception as e:
            logger.error(f"Error updating counters: {e}")
    
    def record_query_time(self, query_time: float):
        """Record a query execution time."""
        self.query_times.append(query_time)
        self.counters["queries_executed"] += 1
        
        if query_time > self.thresholds["slow_query_time"]:
            self.counters["slow_queries"] += 1
    
    def record_memory_operation(self, operation: str):
        """Record a memory operation."""
        if operation == "create":
            self.counters["memories_created"] += 1
        elif operation == "update":
            self.counters["memories_updated"] += 1
        elif operation == "delete":
            self.counters["memories_deleted"] += 1
    
    def record_search(self):
        """Record a search operation."""
        self.counters["searches_performed"] += 1
    
    def record_error(self):
        """Record an error."""
        self.counters["errors_occurred"] += 1
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for the last N hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get metrics from database
            metrics_db_path = self.metrics_dir / "metrics.db"
            conn = sqlite3.connect(metrics_db_path)
            cursor = conn.cursor()
            
            # Get system metrics
            cursor.execute('''
                SELECT metric_name, AVG(value), MIN(value), MAX(value)
                FROM performance_metrics
                WHERE timestamp >= ? AND metric_type = 'system'
                GROUP BY metric_name
            ''', (cutoff_time.isoformat(),))
            
            system_summary = {}
            for row in cursor.fetchall():
                metric_name, avg_val, min_val, max_val = row
                system_summary[metric_name] = {
                    "average": avg_val,
                    "minimum": min_val,
                    "maximum": max_val
                }
            
            # Get database metrics
            cursor.execute('''
                SELECT metric_name, AVG(value), MIN(value), MAX(value)
                FROM performance_metrics
                WHERE timestamp >= ? AND metric_type = 'database'
                GROUP BY metric_name
            ''', (cutoff_time.isoformat(),))
            
            database_summary = {}
            for row in cursor.fetchall():
                metric_name, avg_val, min_val, max_val = row
                database_summary[metric_name] = {
                    "average": avg_val,
                    "minimum": min_val,
                    "maximum": max_val
                }
            
            # Get alerts
            cursor.execute('''
                SELECT alert_type, severity, COUNT(*)
                FROM performance_alerts
                WHERE timestamp >= ? AND resolved = FALSE
                GROUP BY alert_type, severity
            ''', (cutoff_time.isoformat(),))
            
            alerts_summary = {}
            for row in cursor.fetchall():
                alert_type, severity, count = row
                if alert_type not in alerts_summary:
                    alerts_summary[alert_type] = {}
                alerts_summary[alert_type][severity] = count
            
            conn.close()
            
            return {
                "period_hours": hours,
                "system_metrics": system_summary,
                "database_metrics": database_summary,
                "alerts_summary": alerts_summary,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def export_metrics(self, format: str = "json", hours: int = 24) -> str:
        """Export metrics in specified format."""
        try:
            summary = self.get_metrics_summary(hours)
            
            if format.lower() == "json":
                return json.dumps(summary, indent=2)
            elif format.lower() == "csv":
                # Convert to CSV format
                lines = ["Metric,Type,Average,Minimum,Maximum"]
                
                # Add system metrics
                for metric, data in summary.get("system_metrics", {}).items():
                    lines.append(f"{metric},system,{data['average']},{data['minimum']},{data['maximum']}")
                
                # Add database metrics
                for metric, data in summary.get("database_metrics", {}).items():
                    lines.append(f"{metric},database,{data['average']},{data['minimum']},{data['maximum']}")
                
                return "\n".join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return ""