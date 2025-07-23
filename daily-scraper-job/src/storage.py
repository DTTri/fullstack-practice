"""
State management for persistent storage of scraper state.
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import Settings


class StateManager:
    """Manages persistent state for the scraper job."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.state_file = settings.state_file
        self.backup_dir = settings.data_dir / 'backups'
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
    
    def load_state(self) -> Dict[str, Any]:
        """
        Load the previous scraper state from disk.
        
        Returns:
            Dictionary containing previous state, empty dict if no state exists
        """
        if not self.state_file.exists():
            self.logger.info("📂 No previous state file found, starting fresh")
            return {}
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Validate state structure
            if not isinstance(state, dict):
                self.logger.warning("⚠️ Invalid state file format, starting fresh")
                return {}
            
            # Log state info
            articles_count = len(state.get('articles', {}))
            last_run = state.get('last_run', 'Unknown')
            
            self.logger.info(f"📂 Loaded state: {articles_count} articles, last run: {last_run}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load state file: {e}")
            self.logger.info("📂 Starting with empty state")
            return {}
    
    def save_state(self, state: Dict[str, Any]) -> bool:
        """
        Save the current scraper state to disk.
        
        Args:
            state: State dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup of existing state
            if self.state_file.exists():
                self._create_backup()
            
            # Ensure data directory exists
            self.state_file.parent.mkdir(exist_ok=True)
            
            # Add metadata to state
            state_with_meta = {
                **state,
                'saved_at': datetime.now(timezone.utc).isoformat(),
                'version': '1.0'
            }
            
            # Write to temporary file first
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_with_meta, f, indent=2, ensure_ascii=False)
            
            # Atomic move to final location
            temp_file.replace(self.state_file)
            
            articles_count = len(state.get('articles', {}))
            self.logger.info(f"💾 State saved successfully: {articles_count} articles")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save state: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Create a backup of the current state file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"state_backup_{timestamp}.json"
            
            shutil.copy2(self.state_file, backup_file)
            self.logger.debug(f"📋 Created state backup: {backup_file}")
            
            # Clean up old backups (keep last 10)
            self._cleanup_old_backups()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create state backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = list(self.backup_dir.glob('state_backup_*.json'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the 10 most recent backups
            for old_backup in backup_files[10:]:
                old_backup.unlink()
                self.logger.debug(f"🗑️ Removed old backup: {old_backup}")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to cleanup old backups: {e}")
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get information about the current state file.
        
        Returns:
            Dictionary with state file information
        """
        if not self.state_file.exists():
            return {
                'exists': False,
                'size': 0,
                'modified': None,
                'articles_count': 0
            }
        
        try:
            stat = self.state_file.stat()
            state = self.load_state()
            
            return {
                'exists': True,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                'articles_count': len(state.get('articles', {})),
                'last_run': state.get('last_run'),
                'version': state.get('version', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get state info: {e}")
            return {
                'exists': True,
                'error': str(e)
            }
    
    def reset_state(self) -> bool:
        """
        Reset the state by removing the state file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.state_file.exists():
                # Create backup before resetting
                self._create_backup()
                
                # Remove state file
                self.state_file.unlink()
                self.logger.info("🔄 State reset successfully")
                return True
            else:
                self.logger.info("🔄 No state file to reset")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to reset state: {e}")
            return False
    
    def export_state(self, export_path: Path) -> bool:
        """
        Export current state to a specified file.
        
        Args:
            export_path: Path to export the state to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state = self.load_state()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📤 State exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export state: {e}")
            return False
    
    def import_state(self, import_path: Path) -> bool:
        """
        Import state from a specified file.
        
        Args:
            import_path: Path to import the state from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Validate imported state
            if not isinstance(state, dict):
                raise ValueError("Invalid state format")
            
            # Save the imported state
            success = self.save_state(state)
            
            if success:
                self.logger.info(f"📥 State imported from: {import_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Failed to import state: {e}")
            return False
