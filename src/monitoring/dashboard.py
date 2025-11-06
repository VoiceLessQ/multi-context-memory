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
Dashboard for visualizing monitoring metrics in the MCP Multi-Context Memory System.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

from .memory_monitor import MemoryMonitor
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class MonitoringDashboard:
    """Dashboard for visualizing system metrics and performance."""
    
    def __init__(self, db_url: str, session: Optional[Any] = None):
        self.db_url = db_url
        self.session = session
        self.memory_monitor = MemoryMonitor(db_url, session)
        self.performance_monitor = PerformanceMonitor(session) if session else None
        
        # Dashboard configuration
        self.refresh_interval = 60  # seconds
        self.max_data_points = 100  # for charts
        
        # Initialize data storage
        self.historical_data = {
            'memory_usage': [],
            'compression_ratio': [],
            'lazy_loading_ratio': [],
            'response_time': [],
            'error_rate': []
        }
    
    def collect_historical_data(self) -> None:
        """Collect historical data for charts."""
        try:
            # Get current metrics
            memory_stats = self.memory_monitor.get_memory_usage_stats()
            compression_stats = self.memory_monitor.get_compression_stats()
            lazy_loading_stats = self.memory_monitor.get_lazy_loading_stats()
            performance_stats = self.memory_monitor.get_performance_stats()
            
            # Add timestamp
            timestamp = datetime.utcnow()
            
            # Store data points
            self.historical_data['memory_usage'].append({
                'timestamp': timestamp.isoformat(),
                'value': memory_stats.get('total_memories', 0)
            })
            
            self.historical_data['compression_ratio'].append({
                'timestamp': timestamp.isoformat(),
                'value': compression_stats.get('compression_ratio', 0)
            })
            
            self.historical_data['lazy_loading_ratio'].append({
                'timestamp': timestamp.isoformat(),
                'value': lazy_loading_stats.get('lazy_loading_ratio', 0)
            })
            
            self.historical_data['response_time'].append({
                'timestamp': timestamp.isoformat(),
                'value': performance_stats.get('average_query_time_ms', 0)
            })
            
            self.historical_data['error_rate'].append({
                'timestamp': timestamp.isoformat(),
                'value': performance_stats.get('error_rate', 0)
            })
            
            # Limit data points
            for key in self.historical_data:
                if len(self.historical_data[key]) > self.max_data_points:
                    self.historical_data[key] = self.historical_data[key][-self.max_data_points:]
            
            logger.info(f"Collected historical data at {timestamp}")
        
        except Exception as e:
            logger.error(f"Error collecting historical data: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display."""
        try:
            # Collect latest data
            self.collect_historical_data()
            
            # Get current metrics
            memory_stats = self.memory_monitor.get_memory_usage_stats()
            compression_stats = self.memory_monitor.get_compression_stats()
            lazy_loading_stats = self.memory_monitor.get_lazy_loading_stats()
            performance_stats = self.memory_monitor.get_performance_stats()
            alerts = self.memory_monitor.get_alerts()
            
            # Prepare dashboard data
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'total_memories': memory_stats.get('total_memories', 0),
                    'compression_ratio': compression_stats.get('compression_ratio', 0),
                    'lazy_loading_ratio': lazy_loading_stats.get('lazy_loading_ratio', 0),
                    'average_response_time': performance_stats.get('average_query_time_ms', 0),
                    'error_rate': performance_stats.get('error_rate', 0),
                    'total_alerts': len(alerts)
                },
                'charts': {
                    'memory_usage': self.historical_data['memory_usage'][-20:],  # Last 20 points
                    'compression_ratio': self.historical_data['compression_ratio'][-20:],
                    'lazy_loading_ratio': self.historical_data['lazy_loading_ratio'][-20:],
                    'response_time': self.historical_data['response_time'][-20:],
                    'error_rate': self.historical_data['error_rate'][-20:]
                },
                'alerts': alerts,
                'details': {
                    'memory_usage': memory_stats,
                    'compression': compression_stats,
                    'lazy_loading': lazy_loading_stats,
                    'performance': performance_stats
                }
            }
            
            return dashboard_data
        
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard for web display."""
        try:
            dashboard_data = self.get_dashboard_data()
            
            # HTML template
            html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Memory System Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .summary {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
        }
        .summary-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            min-width: 150px;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #666;
        }
        .summary-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .chart-container {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }
        .chart-container h3 {
            margin-top: 0;
            color: #333;
        }
        .alerts {
            margin-top: 30px;
        }
        .alerts h2 {
            color: #333;
        }
        .alert {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid;
        }
        .alert.error {
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }
        .alert.warning {
            background-color: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }
        .alert.info {
            background-color: #d1ecf1;
            border-color: #17a2b8;
            color: #0c5460;
        }
        .last-updated {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>MCP Memory System Dashboard</h1>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Memories</h3>
                <div class="value">{total_memories}</div>
            </div>
            <div class="summary-card">
                <h3>Compression Ratio</h3>
                <div class="value">{compression_ratio:.1%}</div>
            </div>
            <div class="summary-card">
                <h3>Lazy Loading</h3>
                <div class="value">{lazy_loading_ratio:.1%}</div>
            </div>
            <div class="summary-card">
                <h3>Avg Response Time</h3>
                <div class="value">{average_response_time:.1f}ms</div>
            </div>
            <div class="summary-card">
                <h3>Error Rate</h3>
                <div class="value">{error_rate:.1%}</div>
            </div>
            <div class="summary-card">
                <h3>Alerts</h3>
                <div class="value">{total_alerts}</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-container">
                <h3>Memory Usage Over Time</h3>
                <canvas id="memoryChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Compression Ratio Over Time</h3>
                <canvas id="compressionChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Lazy Loading Ratio Over Time</h3>
                <canvas id="lazyLoadingChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Response Time Over Time</h3>
                <canvas id="responseTimeChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Error Rate Over Time</h3>
                <canvas id="errorRateChart"></canvas>
            </div>
        </div>
        
        <div class="alerts">
            <h2>System Alerts</h2>
            {alerts_html}
        </div>
        
        <div class="last-updated">
            Last updated: {timestamp}
        </div>
    </div>
    
    <script>
        // Chart configuration
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };
        
        // Memory Usage Chart
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        new Chart(memoryCtx, {{
            type: 'line',
            data: {{
                labels: {memory_labels},
                datasets: [{{
                    label: 'Total Memories',
                    data: {memory_data},
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }}]
            }},
            options: chartOptions
        }});
        
        // Compression Ratio Chart
        const compressionCtx = document.getElementById('compressionChart').getContext('2d');
        new Chart(compressionCtx, {{
            type: 'line',
            data: {{
                labels: {compression_labels},
                datasets: [{{
                    label: 'Compression Ratio',
                    data: {compression_data},
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    ...chartOptions.scales,
                    y: {{
                        ...chartOptions.scales.y,
                        min: 0,
                        max: 1
                    }}
                }}
            }}
        }});
        
        // Lazy Loading Chart
        const lazyLoadingCtx = document.getElementById('lazyLoadingChart').getContext('2d');
        new Chart(lazyLoadingCtx, {{
            type: 'line',
            data: {{
                labels: {lazy_loading_labels},
                datasets: [{{
                    label: 'Lazy Loading Ratio',
                    data: {lazy_loading_data},
                    borderColor: 'rgb(255, 206, 86)',
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    tension: 0.1
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    ...chartOptions.scales,
                    y: {{
                        ...chartOptions.scales.y,
                        min: 0,
                        max: 1
                    }}
                }}
            }}
        }});
        
        // Response Time Chart
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        new Chart(responseTimeCtx, {{
            type: 'line',
            data: {{
                labels: {response_time_labels},
                datasets: [{{
                    label: 'Response Time (ms)',
                    data: {response_time_data},
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }}]
            }},
            options: chartOptions
        }});
        
        // Error Rate Chart
        const errorRateCtx = document.getElementById('errorRateChart').getContext('2d');
        new Chart(errorRateCtx, {{
            type: 'line',
            data: {{
                labels: {error_rate_labels},
                datasets: [{{
                    label: 'Error Rate',
                    data: {error_rate_data},
                    borderColor: 'rgb(153, 102, 255)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    tension: 0.1
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    ...chartOptions.scales,
                    y: {{
                        ...chartOptions.scales.y,
                        min: 0,
                        max: 1
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
            """
            
            # Prepare data for template
            summary = dashboard_data.get('summary', {})
            charts = dashboard_data.get('charts', {})
            alerts = dashboard_data.get('alerts', [])
            timestamp = dashboard_data.get('timestamp', '')
            
            # Prepare chart data
            def prepare_chart_data(chart_data):
                if not chart_data:
                    return {'labels': [], 'data': []}
                
                labels = [point['timestamp'][-8:] for point in chart_data]  # Time only
                data = [point['value'] for point in chart_data]
                return {'labels': json.dumps(labels), 'data': json.dumps(data)}
            
            memory_chart = prepare_chart_data(charts.get('memory_usage', []))
            compression_chart = prepare_chart_data(charts.get('compression_ratio', []))
            lazy_loading_chart = prepare_chart_data(charts.get('lazy_loading_ratio', []))
            response_time_chart = prepare_chart_data(charts.get('response_time', []))
            error_rate_chart = prepare_chart_data(charts.get('error_rate', []))
            
            # Prepare alerts HTML
            alerts_html = ""
            for alert in alerts:
                alert_class = alert.get('severity', 'info')
                alerts_html += f"""
                <div class="alert {alert_class}">
                    <strong>{alert.get('type', 'Unknown').upper()}:</strong> {alert.get('message', 'No message')}
                    <br><small>{alert.get('timestamp', '')}</small>
                </div>
                """
            
            if not alerts_html:
                alerts_html = "<p>No alerts at this time.</p>"
            
            # Format template data
            template_data = {
                'total_memories': summary.get('total_memories', 0),
                'compression_ratio': summary.get('compression_ratio', 0),
                'lazy_loading_ratio': summary.get('lazy_loading_ratio', 0),
                'average_response_time': summary.get('average_response_time', 0),
                'error_rate': summary.get('error_rate', 0),
                'total_alerts': summary.get('total_alerts', 0),
                'timestamp': timestamp,
                'memory_labels': memory_chart['labels'],
                'memory_data': memory_chart['data'],
                'compression_labels': compression_chart['labels'],
                'compression_data': compression_chart['data'],
                'lazy_loading_labels': lazy_loading_chart['labels'],
                'lazy_loading_data': lazy_loading_chart['data'],
                'response_time_labels': response_time_chart['labels'],
                'response_time_data': response_time_chart['data'],
                'error_rate_labels': error_rate_chart['labels'],
                'error_rate_data': error_rate_chart['data'],
                'alerts_html': alerts_html
            }
            
            # Format the template
            html_dashboard = html_template.format(**template_data)
            
            return html_dashboard
        
        except Exception as e:
            logger.error(f"Error generating HTML dashboard: {e}")
            return f"<html><body><h1>Error generating dashboard</h1><p>{str(e)}</p></body></html>"
    
    def save_dashboard(self, output_path: str) -> bool:
        """Save dashboard to file."""
        try:
            html_dashboard = self.generate_html_dashboard()
            Path(output_path).write_text(html_dashboard, encoding='utf-8')
            logger.info(f"Dashboard saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving dashboard: {e}")
            return False
    
    def get_json_dashboard(self) -> str:
        """Get dashboard data as JSON."""
        try:
            dashboard_data = self.get_dashboard_data()
            return json.dumps(dashboard_data, indent=2)
        except Exception as e:
            logger.error(f"Error getting JSON dashboard: {e}")
            return json.dumps({'error': str(e)}, indent=2)