"""
Monitoring and alerting system for the daily scraper job.
"""

import json
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from config.settings import Settings


class JobMonitor:
    """Monitors job execution and sends alerts."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.metrics_file = settings.data_dir / 'metrics.json'
    
    def record_job_start(self, job_id: str = None) -> str:
        """Record the start of a job execution."""
        if not job_id:
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metrics = {
            'job_id': job_id,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'status': 'running',
            'stats': {}
        }
        
        self._save_metrics(metrics)
        self.logger.info(f"📊 Job monitoring started: {job_id}")
        
        return job_id
    
    def record_job_completion(self, job_id: str, stats: Dict[str, Any], success: bool):
        """Record the completion of a job execution."""
        metrics = self._load_metrics()
        
        if metrics and metrics.get('job_id') == job_id:
            metrics.update({
                'end_time': datetime.now(timezone.utc).isoformat(),
                'status': 'completed' if success else 'failed',
                'success': success,
                'stats': stats
            })
            
            # Calculate execution time
            if 'start_time' in metrics:
                start_time = datetime.fromisoformat(metrics['start_time'])
                end_time = datetime.fromisoformat(metrics['end_time'])
                metrics['execution_time_seconds'] = (end_time - start_time).total_seconds()
            
            self._save_metrics(metrics)
            
            # Send alerts if configured
            if self.settings.alert_on_errors and not success:
                self._send_failure_alert(job_id, stats)
            elif success:
                self._send_success_notification(job_id, stats)
            
            self.logger.info(f"📊 Job monitoring completed: {job_id} ({'success' if success else 'failed'})")
    
    def record_error(self, job_id: str, error: str, context: Dict[str, Any] = None):
        """Record an error during job execution."""
        metrics = self._load_metrics()
        
        if metrics and metrics.get('job_id') == job_id:
            if 'errors' not in metrics:
                metrics['errors'] = []
            
            error_record = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(error),
                'context': context or {}
            }
            
            metrics['errors'].append(error_record)
            self._save_metrics(metrics)
            
            # Check if we should send an alert
            error_count = len(metrics['errors'])
            if error_count >= self.settings.alert_threshold:
                self._send_error_threshold_alert(job_id, error_count)
    
    def get_last_run_metrics(self) -> Optional[Dict[str, Any]]:
        """Get metrics from the last job run."""
        return self._load_metrics()
    
    def get_job_history(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get history of recent job runs."""
        history_file = self.settings.data_dir / 'job_history.json'
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # Return most recent jobs first
            return sorted(history, key=lambda x: x.get('start_time', ''), reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load job history: {e}")
            return []
    
    def archive_current_metrics(self):
        """Archive current metrics to job history."""
        metrics = self._load_metrics()
        
        if not metrics:
            return
        
        history_file = self.settings.data_dir / 'job_history.json'
        
        try:
            # Load existing history
            history = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Add current metrics to history
            history.append(metrics)
            
            # Keep only last 100 runs
            history = history[-100:]
            
            # Save updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"📚 Archived metrics to job history")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to archive metrics: {e}")
    
    def _load_metrics(self) -> Optional[Dict[str, Any]]:
        """Load current metrics from file."""
        if not self.metrics_file.exists():
            return None
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Failed to load metrics: {e}")
            return None
    
    def _save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to file."""
        try:
            self.settings.data_dir.mkdir(exist_ok=True)
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save metrics: {e}")
    
    def _send_failure_alert(self, job_id: str, stats: Dict[str, Any]):
        """Send alert for job failure."""
        if not self.settings.webhook_url:
            return
        
        message = {
            'type': 'job_failure',
            'job_id': job_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stats': stats,
            'message': f"❌ Daily scraper job {job_id} failed"
        }
        
        self._send_webhook(message)
    
    def _send_success_notification(self, job_id: str, stats: Dict[str, Any]):
        """Send notification for successful job completion."""
        if not self.settings.webhook_url:
            return
        
        # Only send success notifications for significant changes
        total_changes = stats.get('added', 0) + stats.get('updated', 0)
        if total_changes == 0:
            return  # Skip notification for no-change runs
        
        message = {
            'type': 'job_success',
            'job_id': job_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stats': stats,
            'message': f"✅ Daily scraper job {job_id} completed successfully"
        }
        
        self._send_webhook(message)
    
    def _send_error_threshold_alert(self, job_id: str, error_count: int):
        """Send alert when error threshold is reached."""
        if not self.settings.webhook_url:
            return
        
        message = {
            'type': 'error_threshold',
            'job_id': job_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_count': error_count,
            'threshold': self.settings.alert_threshold,
            'message': f"⚠️ Job {job_id} has reached error threshold ({error_count} errors)"
        }
        
        self._send_webhook(message)
    
    def _send_webhook(self, message: Dict[str, Any]):
        """Send webhook notification."""
        try:
            response = requests.post(
                self.settings.webhook_url,
                json=message,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            self.logger.debug(f"📡 Webhook sent successfully: {message['type']}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send webhook: {e}")
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Generate a comprehensive status report."""
        metrics = self._load_metrics()
        history = self.get_job_history(5)
        
        report = {
            'current_job': metrics,
            'recent_history': history,
            'summary': {
                'total_runs': len(history),
                'successful_runs': len([h for h in history if h.get('success', False)]),
                'failed_runs': len([h for h in history if not h.get('success', True)]),
                'last_run_time': history[0].get('start_time') if history else None,
                'last_success_time': None,
                'average_execution_time': 0
            }
        }
        
        # Calculate summary statistics
        if history:
            successful_runs = [h for h in history if h.get('success', False)]
            if successful_runs:
                report['summary']['last_success_time'] = successful_runs[0].get('start_time')
            
            # Calculate average execution time
            execution_times = [h.get('execution_time_seconds', 0) for h in history if h.get('execution_time_seconds')]
            if execution_times:
                report['summary']['average_execution_time'] = sum(execution_times) / len(execution_times)
        
        return report
