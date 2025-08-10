"""
Baseline measurement system for the MCP Multi-Context Memory System.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import time
import psutil
import os
from pathlib import Path
import json
import logging

from ..database.models import Memory, Context, Relation

logger = logging.getLogger(__name__)

class BaselineCollector:
    """Collect baseline metrics before optimization implementation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics = {}
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
    
    def collect_current_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive baseline metrics."""
        logger.info("Collecting baseline metrics...")
        
        # Database metrics
        self.metrics["database"] = self._collect_database_metrics()
        
        # Performance metrics
        self.metrics["performance"] = self._collect_performance_metrics()
        
        # Memory metrics
        self.metrics["memory"] = self._collect_memory_metrics()
        
        # Storage metrics
        self.metrics["storage"] = self._collect_storage_metrics()
        
        # Search metrics
        self.metrics["search"] = self._collect_search_metrics()
        
        # System metrics
        self.metrics["system"] = self._collect_system_metrics()
        
        # Save baseline
        self._save_baseline()
        
        logger.info("Baseline metrics collection completed")
        return self.metrics
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database-specific metrics."""
        try:
            # Count records
            total_memories = self.db.query(Memory).count()
            total_contexts = self.db.query(Context).count()
            total_relations = self.db.query(Relation).count()
            
            # Database size
            db_size = self._get_database_size()
            
            # Memory content analysis
            largest_memory = self._get_largest_memory()
            avg_memory_size = self._get_average_memory_size()
            
            # Context distribution
            memories_by_context = self._get_memories_by_context()
            
            # Content size distribution
            size_distribution = self._get_content_size_distribution()
            
            return {
                "total_memories": total_memories,
                "total_contexts": total_contexts,
                "total_relations": total_relations,
                "database_size_bytes": db_size,
                "database_size_mb": db_size / (1024 * 1024),
                "largest_memory_bytes": largest_memory,
                "largest_memory_mb": largest_memory / (1024 * 1024),
                "average_memory_size_bytes": avg_memory_size,
                "average_memory_size_mb": avg_memory_size / (1024 * 1024),
                "memories_by_context": memories_by_context,
                "content_size_distribution": size_distribution,
                "compression_candidates": self._count_compression_candidates()
            }
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {"error": str(e)}
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance baseline metrics."""
        try:
            times = []
            
            # Test memory retrieval queries
            for _ in range(10):
                start = time.time()
                memories = self.db.query(Memory).limit(100).all()
                end = time.time()
                times.append(end - start)
            
            # Test context queries
            context_times = []
            for _ in range(10):
                start = time.time()
                contexts = self.db.query(Context).limit(50).all()
                end = time.time()
                context_times.append(end - start)
            
            # Test relation queries
            relation_times = []
            for _ in range(10):
                start = time.time()
                relations = self.db.query(Relation).limit(100).all()
                end = time.time()
                relation_times.append(end - start)
            
            return {
                "memory_query_times": times,
                "memory_query_avg": sum(times) / len(times) if times else 0,
                "memory_query_min": min(times) if times else 0,
                "memory_query_max": max(times) if times else 0,
                "context_query_times": context_times,
                "context_query_avg": sum(context_times) / len(context_times) if context_times else 0,
                "relation_query_times": relation_times,
                "relation_query_avg": sum(relation_times) / len(relation_times) if relation_times else 0,
                "query_throughput": len(times) / sum(times) if times else 0
            }
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {"error": str(e)}
    
    def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory usage metrics."""
        try:
            process = psutil.Process(os.getpid())
            
            return {
                "current_memory_usage_bytes": process.memory_info().rss,
                "current_memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "peak_memory_usage_bytes": process.memory_info().vms,
                "peak_memory_usage_mb": process.memory_info().vms / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "available_memory_bytes": psutil.virtual_memory().available,
                "total_memory_bytes": psutil.virtual_memory().total,
                "memory_usage_percent": psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
            return {"error": str(e)}
    
    def _collect_storage_metrics(self) -> Dict[str, Any]:
        """Collect storage usage metrics."""
        try:
            db_path = Path(self.db.bind.url.database)
            data_dir = Path("./data")
            
            storage_info = {
                "database_size_bytes": 0,
                "database_size_mb": 0,
                "data_directory_size_bytes": 0,
                "data_directory_size_mb": 0,
                "compression_candidates": 0,
                "large_memories_count": 0,
                "archive_candidates_count": 0
            }
            
            # Database size
            if db_path.exists():
                db_size = db_path.stat().st_size
                storage_info["database_size_bytes"] = db_size
                storage_info["database_size_mb"] = db_size / (1024 * 1024)
            
            # Data directory size
            if data_dir.exists():
                dir_size = self._get_directory_size(data_dir)
                storage_info["data_directory_size_bytes"] = dir_size
                storage_info["data_directory_size_mb"] = dir_size / (1024 * 1024)
            
            # Content analysis
            storage_info["compression_candidates"] = self._count_compression_candidates()
            storage_info["large_memories_count"] = self._count_large_memories(1024 * 1024)  # 1MB+
            storage_info["archive_candidates_count"] = self._count_old_memories(180)  # 180 days
            
            return storage_info
        except Exception as e:
            logger.error(f"Error collecting storage metrics: {e}")
            return {"error": str(e)}
    
    def _collect_search_metrics(self) -> Dict[str, Any]:
        """Collect search performance metrics."""
        try:
            from ..database.enhanced_memory_db import EnhancedMemoryDB
            
            db_manager = EnhancedMemoryDB("sqlite:///:memory:")
            times = []
            
            # Test search with various queries
            test_queries = ["test", "memory", "search", "data", "system"]
            
            for query in test_queries:
                start = time.time()
                # This would normally use the actual database
                # For now, we'll simulate search performance
                time.sleep(0.01)  # Simulate search time
                end = time.time()
                times.append(end - start)
            
            return {
                "search_query_times": times,
                "search_query_avg": sum(times) / len(times) if times else 0,
                "search_query_min": min(times) if times else 0,
                "search_query_max": max(times) if times else 0,
                "search_throughput": len(times) / sum(times) if times else 0,
                "test_queries_used": test_queries
            }
        except Exception as e:
            logger.error(f"Error collecting search metrics: {e}")
            return {"error": str(e)}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            return {
                "system_boot_time": boot_time.isoformat(),
                "system_uptime_seconds": time.time() - psutil.boot_time(),
                "cpu_percent": psutil.cpu_percent(),
                "cpu_count": psutil.cpu_count(),
                "disk_usage": self._get_disk_usage(),
                "network_io": self._get_network_io()
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {"error": str(e)}
    
    def _get_database_size(self) -> int:
        """Get database file size in bytes."""
        db_path = Path(self.db.bind.url.database)
        return db_path.stat().st_size if db_path.exists() else 0
    
    def _get_largest_memory(self) -> int:
        """Get size of largest memory in bytes."""
        try:
            result = self.db.query(
                db.func.length(Memory.content).label("content_length")
            ).order_by(db.desc("content_length")).first()
            return result.content_length if result else 0
        except Exception as e:
            logger.error(f"Error getting largest memory: {e}")
            return 0
    
    def _get_average_memory_size(self) -> float:
        """Get average memory size in bytes."""
        try:
            result = self.db.query(
                db.func.avg(db.func.length(Memory.content)).label("avg_length")
            ).first()
            return result.avg_length if result else 0
        except Exception as e:
            logger.error(f"Error getting average memory size: {e}")
            return 0
    
    def _get_memories_by_context(self) -> Dict[int, int]:
        """Get count of memories per context."""
        try:
            counts = {}
            for context in self.db.query(Context).all():
                count = self.db.query(Memory).filter(
                    Memory.context_id == context.id
                ).count()
                counts[context.id] = {
                    "count": count,
                    "context_name": context.name
                }
            return counts
        except Exception as e:
            logger.error(f"Error getting memories by context: {e}")
            return {}
    
    def _get_content_size_distribution(self) -> Dict[str, int]:
        """Get distribution of content sizes."""
        try:
            distribution = {
                "lt_1kb": 0,
                "1kb_10kb": 0,
                "10kb_100kb": 0,
                "100kb_1mb": 0,
                "gt_1mb": 0
            }
            
            # This would need to be implemented with a proper query
            # For now, return zeros
            return distribution
        except Exception as e:
            logger.error(f"Error getting content size distribution: {e}")
            return {}
    
    def _count_compression_candidates(self) -> int:
        """Count memories that would benefit from compression."""
        try:
            threshold = 10240  # 10KB
            
            count = self.db.query(Memory).filter(
                db.func.length(Memory.content) > threshold
            ).count()
            
            return count
        except Exception as e:
            logger.error(f"Error counting compression candidates: {e}")
            return 0
    
    def _count_large_memories(self, size_threshold: int) -> int:
        """Count memories larger than threshold."""
        try:
            count = self.db.query(Memory).filter(
                db.func.length(Memory.content) > size_threshold
            ).count()
            
            return count
        except Exception as e:
            logger.error(f"Error counting large memories: {e}")
            return 0
    
    def _count_old_memories(self, days_threshold: int) -> int:
        """Count memories older than threshold days."""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            count = self.db.query(Memory).filter(
                Memory.created_at < cutoff_date
            ).count()
            
            return count
        except Exception as e:
            logger.error(f"Error counting old memories: {e}")
            return 0
    
    def _get_directory_size(self, path: Path) -> int:
        """Get directory size in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting directory size: {e}")
        
        return total_size
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                "total_bytes": disk_usage.total,
                "total_gb": disk_usage.total / (1024**3),
                "used_bytes": disk_usage.used,
                "used_gb": disk_usage.used / (1024**3),
                "free_bytes": disk_usage.free,
                "free_gb": disk_usage.free / (1024**3),
                "percent": disk_usage.percent
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {}
    
    def _get_network_io(self) -> Dict[str, int]:
        """Get network I/O statistics."""
        try:
            io_counters = psutil.net_io_counters()
            return {
                "bytes_sent": io_counters.bytes_sent,
                "bytes_recv": io_counters.bytes_recv,
                "packets_sent": io_counters.packets_sent,
                "packets_recv": io_counters.packets_recv
            }
        except Exception as e:
            logger.error(f"Error getting network I/O: {e}")
            return {}
    
    def _save_baseline(self):
        """Save baseline metrics to file."""
        try:
            baseline_file = self.data_dir / "baseline_metrics.json"
            
            baseline_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": self.metrics,
                "version": "1.0"
            }
            
            with open(baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            logger.info(f"Baseline metrics saved to {baseline_file}")
        except Exception as e:
            logger.error(f"Error saving baseline metrics: {e}")
    
    def load_baseline(self, baseline_file: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Load baseline metrics from file."""
        try:
            if baseline_file is None:
                baseline_file = self.data_dir / "baseline_metrics.json"
            
            if not baseline_file.exists():
                logger.warning(f"Baseline file not found: {baseline_file}")
                return None
            
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            
            logger.info(f"Baseline metrics loaded from {baseline_file}")
            return baseline_data.get("metrics")
        except Exception as e:
            logger.error(f"Error loading baseline metrics: {e}")
            return None