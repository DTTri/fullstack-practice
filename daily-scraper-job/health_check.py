#!/usr/bin/env python3
"""
Health check endpoint for the daily scraper job.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "config"))

from config.settings import Settings
from src.monitoring import JobMonitor


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""
    
    def __init__(self, *args, **kwargs):
        self.settings = Settings()
        self.monitor = JobMonitor(self.settings)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self._handle_health_check()
        elif self.path == '/status':
            self._handle_status_check()
        elif self.path == '/metrics':
            self._handle_metrics()
        else:
            self._send_response(404, {'error': 'Not found'})
    
    def _handle_health_check(self):
        """Basic health check - always returns OK if service is running."""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': 'daily-scraper-job',
            'version': '1.0.0'
        }
        self._send_response(200, health_data)
    
    def _handle_status_check(self):
        """Detailed status check including last job results."""
        try:
            status_report = self.monitor.generate_status_report()
            
            # Determine overall status
            last_job = status_report.get('current_job')
            recent_history = status_report.get('recent_history', [])
            
            if last_job and last_job.get('status') == 'running':
                overall_status = 'running'
            elif recent_history and recent_history[0].get('success', False):
                overall_status = 'healthy'
            elif recent_history:
                overall_status = 'degraded'
            else:
                overall_status = 'unknown'
            
            status_data = {
                'status': overall_status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'daily-scraper-job',
                'version': '1.0.0',
                'details': status_report
            }
            
            self._send_response(200, status_data)
            
        except Exception as e:
            error_data = {
                'status': 'error',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
            self._send_response(500, error_data)
    
    def _handle_metrics(self):
        """Return metrics in Prometheus format."""
        try:
            status_report = self.monitor.generate_status_report()
            
            # Generate Prometheus metrics
            metrics = []
            
            # Job execution metrics
            summary = status_report.get('summary', {})
            metrics.append(f"scraper_total_runs {summary.get('total_runs', 0)}")
            metrics.append(f"scraper_successful_runs {summary.get('successful_runs', 0)}")
            metrics.append(f"scraper_failed_runs {summary.get('failed_runs', 0)}")
            metrics.append(f"scraper_average_execution_time {summary.get('average_execution_time', 0)}")
            
            # Last job metrics
            last_job = status_report.get('current_job')
            if last_job and last_job.get('stats'):
                stats = last_job['stats']
                metrics.append(f"scraper_last_total_articles {stats.get('total_articles', 0)}")
                metrics.append(f"scraper_last_added_articles {stats.get('added', 0)}")
                metrics.append(f"scraper_last_updated_articles {stats.get('updated', 0)}")
                metrics.append(f"scraper_last_skipped_articles {stats.get('skipped', 0)}")
                metrics.append(f"scraper_last_errors {stats.get('errors', 0)}")
            
            # Service status
            metrics.append(f"scraper_service_up 1")
            
            response_text = '\n'.join(metrics) + '\n'
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(response_text)))
            self.end_headers()
            self.wfile.write(response_text.encode('utf-8'))
            
        except Exception as e:
            error_text = f"# Error generating metrics: {str(e)}\nscraper_service_up 0\n"
            
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(error_text)))
            self.end_headers()
            self.wfile.write(error_text.encode('utf-8'))
    
    def _send_response(self, status_code: int, data: dict):
        """Send JSON response."""
        response_text = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_text)))
        self.end_headers()
        self.wfile.write(response_text.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass


def run_health_server(port: int = 8080):
    """Run the health check server."""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    print(f"Endpoints:")
    print(f"  GET /health  - Basic health check")
    print(f"  GET /status  - Detailed status with job history")
    print(f"  GET /metrics - Prometheus metrics")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down health check server...")
        server.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Health check server for daily scraper job")
    parser.add_argument('--port', type=int, default=8080, help='Port to run server on')
    
    args = parser.parse_args()
    run_health_server(args.port)
