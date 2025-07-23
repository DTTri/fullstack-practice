"""
Configuration settings for the daily scraper job.
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        
        # Scraping Configuration
        self.base_url: str = 'https://support.optisigns.com'
        self.max_articles: Optional[int] = self._get_int_env('MAX_ARTICLES')
        self.request_delay: float = float(os.getenv('REQUEST_DELAY', '1.0'))
        self.max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
        
        # Vector Store Configuration
        self.vector_store_name: str = os.getenv('VECTOR_STORE_NAME', 'OptiSigns Support Articles')
        self.assistant_name: str = os.getenv('ASSISTANT_NAME', 'OptiBot')
        self.chunk_size: int = int(os.getenv('CHUNK_SIZE', '8000'))
        self.min_chunk_size: int = int(os.getenv('MIN_CHUNK_SIZE', '100'))
        
        # Job Configuration
        self.dry_run: bool = os.getenv('DRY_RUN', 'false').lower() == 'true'
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # File Paths
        self.project_root: Path = Path(__file__).parent.parent
        self.data_dir: Path = self.project_root / 'data'
        self.logs_dir: Path = self.project_root / 'logs'
        self.state_file: Path = self.data_dir / 'scraper_state.json'
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Delta Detection Configuration
        self.enable_hash_detection: bool = os.getenv('ENABLE_HASH_DETECTION', 'true').lower() == 'true'
        self.enable_lastmod_detection: bool = os.getenv('ENABLE_LASTMOD_DETECTION', 'true').lower() == 'true'
        self.force_full_update: bool = os.getenv('FORCE_FULL_UPDATE', 'false').lower() == 'true'
        
        # Rate Limiting
        self.api_rate_limit: float = float(os.getenv('API_RATE_LIMIT', '0.5'))
        self.batch_size: int = int(os.getenv('BATCH_SIZE', '10'))
        
        # Monitoring and Alerting
        self.webhook_url: Optional[str] = os.getenv('WEBHOOK_URL')
        self.alert_on_errors: bool = os.getenv('ALERT_ON_ERRORS', 'true').lower() == 'true'
        self.alert_threshold: int = int(os.getenv('ALERT_THRESHOLD', '5'))
    
    def _get_int_env(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer environment variable with optional default."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.dry_run and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when not in dry-run mode")
        
        if self.max_articles is not None and self.max_articles <= 0:
            errors.append("MAX_ARTICLES must be positive")
        
        if self.request_delay < 0:
            errors.append("REQUEST_DELAY must be non-negative")
        
        if self.max_retries < 0:
            errors.append("MAX_RETRIES must be non-negative")
        
        if self.chunk_size <= 0:
            errors.append("CHUNK_SIZE must be positive")
        
        if self.min_chunk_size <= 0:
            errors.append("MIN_CHUNK_SIZE must be positive")
        
        if self.chunk_size <= self.min_chunk_size:
            errors.append("CHUNK_SIZE must be greater than MIN_CHUNK_SIZE")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary for logging."""
        return {
            'base_url': self.base_url,
            'max_articles': self.max_articles,
            'request_delay': self.request_delay,
            'max_retries': self.max_retries,
            'vector_store_name': self.vector_store_name,
            'assistant_name': self.assistant_name,
            'chunk_size': self.chunk_size,
            'min_chunk_size': self.min_chunk_size,
            'dry_run': self.dry_run,
            'log_level': self.log_level,
            'enable_hash_detection': self.enable_hash_detection,
            'enable_lastmod_detection': self.enable_lastmod_detection,
            'force_full_update': self.force_full_update,
            'api_rate_limit': self.api_rate_limit,
            'batch_size': self.batch_size,
            'alert_on_errors': self.alert_on_errors,
            'alert_threshold': self.alert_threshold
        }
