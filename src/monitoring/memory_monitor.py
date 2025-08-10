"""
Memory monitoring tools for the MCP Multi-Context Memory System.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json

from ..database.models import Memory, Context, Relation
from ..database.enhanced_memory_db import EnhancedMemoryDB
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitor memory usage, performance, and optimization metrics."""
    
    def __init__(self, db_url: str, session: Optional[Session] = None):
        self.db_url = db_url
        self.session = session
        self.performance_monitor = PerformanceMonitor(session) if session else None
        self.enhanced_db = EnhancedMemoryDB(db_url, session)
        
        # Monitoring thresholds
        self.compression_threshold = 0.1  # 10% compression ratio minimum
        self.lazy_loading_threshold = 0.2  # 20% of memories should be lazy loaded
        self.performance_threshold = 100  # 100ms response time threshold
        
        # Alert thresholds
        self.alert_thresholds = {
            "high_memory_usage": 0.8,  # 80% of available memory
            "low_compression_ratio": 0.05,  # 5% compression ratio
            "high_error_rate": 0.05,  # 5% error rate
            "slow_response_time": 0.5,  # 500ms response time
            "low_lazy_loading_ratio": 0.1,  # 10% lazy loading ratio
        }
    
    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            # Get total memory count
            total_memories = self.session.query(Memory).count()
            
            # Get memory by size
            size_stats = self.session.query(
                func.count(Memory.id).label('count'),
                func.sum(func.length(Memory.content)).label('total_size')
            ).group_by(
                func.case(
                    (func.length(Memory.content) < 1024, 'small'),
                    (func.length(Memory.content) < 10240, 'medium'),
                    else_='large'
                )
            ).all()
            
            # Calculate size distribution
            size_distribution = {
                'small': 0,  # < 1KB
                'medium': 0,  # 1KB - 10KB
                'large': 0,   # > 10KB
                'total_size': 0
            }
            
            for stat in size_stats:
                if stat.count > 0:
                    size_distribution['small'] += stat.count if 'small' in str(stat.count) else 0
                    size_distribution['medium'] += stat.count if 'medium' in str(stat.count) else 0
                    size_distribution['large'] += stat.count if 'large' in str(stat.count) else 0
                    size_distribution['total_size'] = stat.total_size or 0
            
            # Get memory by age
            now = datetime.utcnow()
            age_stats = self.session.query(
                func.count(Memory.id).label('count'),
                func.max(Memory.created_at).label('latest')
            ).filter(
                Memory.created_at >= now - timedelta(days=30)
            ).first()
            
            return {
                'total_memories': total_memories,
                'size_distribution': size_distribution,
                'recent_memories_30d': age_stats.count if age_stats else 0,
                'latest_memory': age_stats.latest.isoformat() if age_stats and age_stats.latest else None,
                'average_size_bytes': size_distribution['total_size'] / max(total_memories, 1)
            }
        
        except Exception as e:
            logger.error(f"Error getting memory usage stats: {e}")
            return {}
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics and effectiveness."""
        try:
            # Get total memories
            total_memories = self.session.query(Memory).count()
            
            # Get compressed memories
            compressed_memories = self.session.query(Memory).filter(
                Memory.content_compressed == True
            ).count()
            
            # Calculate compression ratio
            compression_ratio = compressed_memories / max(total_memories, 1)
            
            # Get compression effectiveness
            compression_effectiveness = self.session.query(
                func.count(Memory.id).label('count'),
                func.sum(func.length(Memory.content)).label('original_size'),
                func.sum(func.length(func.substr(Memory.content, 1, 100))).label('compressed_size')
            ).filter(
                Memory.content_compressed == True
            ).first()
            
            # Calculate savings
            original_size = compression_effectiveness.original_size if compression_effectiveness else 0
            compressed_size = compression_effectiveness.compressed_size if compression_effectiveness else 0
            savings = original_size - compressed_size
            savings_ratio = savings / max(original_size, 1)
            
            # Check compression effectiveness
            is_effective = savings_ratio >= self.compression_threshold
            
            return {
                'total_memories': total_memories,
                'compressed_memories': compressed_memories,
                'compression_ratio': compression_ratio,
                'original_size_bytes': original_size,
                'compressed_size_bytes': compressed_size,
                'savings_bytes': savings,
                'savings_ratio': savings_ratio,
                'is_effective': is_effective,
                'recommendation': 'Increase compression' if not is_effective else 'Compression is effective'
            }
        
        except Exception as e:
            logger.error(f"Error getting compression stats: {e}")
            return {}
    
    def get_lazy_loading_stats(self) -> Dict[str, Any]:
        """Get lazy loading statistics and effectiveness."""
        try:
            # Get total memories
            total_memories = self.session.query(Memory).count()
            
            # Get lazy loaded memories (those with _content_loaded = False)
            lazy_loaded_memories = self.session.query(Memory).filter(
                Memory.content_compressed == True
            ).count()
            
            # Calculate lazy loading ratio
            lazy_loading_ratio = lazy_loaded_memories / max(total_memories, 1)
            
            # Check lazy loading effectiveness
            is_effective = lazy_loading_ratio >= self.lazy_loading_threshold
            
            return {
                'total_memories': total_memories,
                'lazy_loaded_memories': lazy_loaded_memories,
                'lazy_loading_ratio': lazy_loading_ratio,
                'is_effective': is_effective,
                'recommendation': 'Increase lazy loading' if not is_effective else 'Lazy loading is effective'
            }
        
        except Exception as e:
            logger.error(f"Error getting lazy loading stats: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics and metrics."""
        try:
            if not self.performance_monitor:
                return {}
            
            # Get performance metrics
            metrics = self.performance_monitor.get_metrics_summary(hours=1)
            
            # Calculate average response time
            avg_response_time = metrics.get('average_query_time', 0)
            
            # Check performance
            is_performant = avg_response_time <= self.performance_threshold
            
            return {
                'average_query_time_ms': avg_response_time,
                'is_performant': is_performant,
                'recommendation': 'Optimize queries' if not is_performant else 'Performance is good',
                'total_queries': metrics.get('total_queries', 0),
                'error_rate': metrics.get('error_rate', 0)
            }
        
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts based on thresholds."""
        alerts = []
        
        try:
            # Check memory usage
            memory_stats = self.get_memory_usage_stats()
            if memory_stats.get('total_memories', 0) > 0:
                memory_usage = memory_stats.get('average_size_bytes', 0) / 1024 / 1024  # Convert to MB
                if memory_usage > self.alert_thresholds['high_memory_usage']:
                    alerts.append({
                        'type': 'memory_usage',
                        'severity': 'warning',
                        'message': f'High memory usage: {memory_usage:.2f}MB',
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            # Check compression ratio
            compression_stats = self.get_compression_stats()
            if compression_stats.get('savings_ratio', 0) < self.alert_thresholds['low_compression_ratio']:
                alerts.append({
                    'type': 'compression_ratio',
                    'severity': 'warning',
                    'message': f'Low compression ratio: {compression_stats.get("savings_ratio", 0):.2%}',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check error rate
            performance_stats = self.get_performance_stats()
            if performance_stats.get('error_rate', 0) > self.alert_thresholds['high_error_rate']:
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'error',
                    'message': f'High error rate: {performance_stats.get("error_rate", 0):.2%}',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check response time
            if performance_stats.get('average_query_time_ms', 0) > self.alert_thresholds['slow_response_time'] * 1000:
                alerts.append({
                    'type': 'response_time',
                    'severity': 'warning',
                    'message': f'Slow response time: {performance_stats.get("average_query_time_ms", 0):.2f}ms',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check lazy loading ratio
            lazy_loading_stats = self.get_lazy_loading_stats()
            if lazy_loading_stats.get('lazy_loading_ratio', 0) < self.alert_thresholds['low_lazy_loading_ratio']:
                alerts.append({
                    'type': 'lazy_loading_ratio',
                    'severity': 'info',
                    'message': f'Low lazy loading ratio: {lazy_loading_stats.get("lazy_loading_ratio", 0):.2%}',
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            alerts.append({
                'type': 'system_error',
                'severity': 'error',
                'message': f'Error getting alerts: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive monitoring report."""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'memory_usage': self.get_memory_usage_stats(),
                'compression': self.get_compression_stats(),
                'lazy_loading': self.get_lazy_loading_stats(),
                'performance': self.get_performance_stats(),
                'alerts': self.get_alerts(),
                'recommendations': []
            }
            
            # Generate recommendations based on stats
            if not report['compression'].get('is_effective', False):
                report['recommendations'].append('Consider adjusting compression settings')
            
            if not report['lazy_loading'].get('is_effective', False):
                report['recommendations'].append('Consider enabling more lazy loading')
            
            if not report['performance'].get('is_performant', False):
                report['recommendations'].append('Consider optimizing database queries')
            
            if report['alerts']:
                report['recommendations'].append('Review system alerts for potential issues')
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        try:
            report = self.generate_report()
            
            if format.lower() == "json":
                return json.dumps(report, indent=2)
            elif format.lower() == "csv":
                # Convert to CSV format
                csv_lines = []
                csv_lines.append("Metric,Value")
                
                # Add basic metrics
                csv_lines.append(f"Total Memories,{report['memory_usage'].get('total_memories', 0)}")
                csv_lines.append(f"Compression Ratio,{report['compression'].get('compression_ratio', 0):.2%}")
                csv_lines.append(f"Lazy Loading Ratio,{report['lazy_loading'].get('lazy_loading_ratio', 0):.2%}")
                csv_lines.append(f"Average Query Time,{report['performance'].get('average_query_time_ms', 0):.2f}ms")
                csv_lines.append(f"Error Rate,{report['performance'].get('error_rate', 0):.2%}")
                
                # Add alerts
                csv_lines.append(f"Total Alerts,{len(report['alerts'])}")
                for alert in report['alerts']:
                    csv_lines.append(f"Alert,{alert['type']},{alert['severity']},{alert['message']}")
                
                return "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return ""