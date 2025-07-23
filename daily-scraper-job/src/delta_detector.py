"""
Delta detection system for identifying new, updated, and unchanged articles.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Any, Optional
# from dateutil import parser as date_parser

from config.settings import Settings


class DeltaDetector:
    """Detects changes between previous and current article states."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def detect_changes(self, previous_articles: Dict[str, Any], current_articles: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """
        Detect changes between previous and current article states.
        
        Args:
            previous_articles: Dictionary of previous article states (id -> metadata)
            current_articles: List of current article data
            
        Returns:
            Dictionary with sets of article IDs for 'added', 'updated', 'unchanged'
        """
        self.logger.info("🔍 Starting delta detection...")
        
        # Convert current articles to lookup dict
        current_lookup = {article['id']: article for article in current_articles}
        
        # Get article ID sets
        previous_ids = set(previous_articles.keys())
        current_ids = set(current_lookup.keys())
        
        # Find added and removed articles
        added_ids = current_ids - previous_ids
        removed_ids = previous_ids - current_ids
        common_ids = current_ids & previous_ids
        
        self.logger.info(f"📊 Article counts: {len(current_ids)} current, {len(previous_ids)} previous")
        self.logger.info(f"➕ New articles: {len(added_ids)}")
        self.logger.info(f"➖ Removed articles: {len(removed_ids)}")
        self.logger.info(f"🔄 Common articles: {len(common_ids)}")
        
        if removed_ids:
            self.logger.warning(f"⚠️ Articles no longer found: {list(removed_ids)[:5]}{'...' if len(removed_ids) > 5 else ''}")
        
        # Check for updates in common articles
        updated_ids = set()
        unchanged_ids = set()
        
        if self.settings.force_full_update:
            self.logger.info("🔄 Force full update enabled - treating all common articles as updated")
            updated_ids = common_ids
        else:
            for article_id in common_ids:
                if self._is_article_updated(previous_articles[article_id], current_lookup[article_id]):
                    updated_ids.add(article_id)
                else:
                    unchanged_ids.add(article_id)
        
        self.logger.info(f"🔄 Updated articles: {len(updated_ids)}")
        self.logger.info(f"⏭️ Unchanged articles: {len(unchanged_ids)}")
        
        # Log sample of changes for debugging
        if added_ids:
            sample_added = list(added_ids)[:3]
            self.logger.debug(f"Sample added articles: {sample_added}")
        
        if updated_ids:
            sample_updated = list(updated_ids)[:3]
            self.logger.debug(f"Sample updated articles: {sample_updated}")
            
            # Log details of first updated article
            if sample_updated:
                first_updated = sample_updated[0]
                prev_meta = previous_articles[first_updated]
                curr_article = current_lookup[first_updated]
                self.logger.debug(f"Update details for {first_updated}:")
                self.logger.debug(f"  Previous hash: {prev_meta.get('hash', 'N/A')}")
                self.logger.debug(f"  Current hash: {curr_article.get('content_hash', 'N/A')}")
                self.logger.debug(f"  Previous last_modified: {prev_meta.get('last_modified', 'N/A')}")
                self.logger.debug(f"  Current last_modified: {curr_article.get('last_modified', 'N/A')}")
        
        return {
            'added': added_ids,
            'updated': updated_ids,
            'unchanged': unchanged_ids,
            'removed': removed_ids
        }
    
    def _is_article_updated(self, previous_meta: Dict[str, Any], current_article: Dict[str, Any]) -> bool:
        """
        Check if an article has been updated based on available detection methods.
        
        Args:
            previous_meta: Previous article metadata
            current_article: Current article data
            
        Returns:
            True if article has been updated, False otherwise
        """
        # Hash-based detection (most reliable)
        if self.settings.enable_hash_detection:
            prev_hash = previous_meta.get('hash')
            curr_hash = current_article.get('content_hash')
            
            if prev_hash and curr_hash:
                if prev_hash != curr_hash:
                    self.logger.debug(f"Hash change detected for {current_article['id']}")
                    return True
            elif not prev_hash and curr_hash:
                # Previous run didn't have hash, assume updated
                self.logger.debug(f"No previous hash for {current_article['id']}, assuming updated")
                return True
        
        # Last-Modified header detection
        if self.settings.enable_lastmod_detection:
            prev_lastmod = previous_meta.get('last_modified')
            curr_lastmod = current_article.get('last_modified')
            
            if prev_lastmod and curr_lastmod:
                try:
                    prev_dt = self._parse_date(prev_lastmod)
                    curr_dt = self._parse_date(curr_lastmod)
                    
                    if curr_dt > prev_dt:
                        self.logger.debug(f"Last-Modified change detected for {current_article['id']}")
                        return True
                except Exception as e:
                    self.logger.warning(f"Failed to parse dates for {current_article['id']}: {e}")
        
        # Title change detection (fallback)
        prev_title = previous_meta.get('title', '').strip()
        curr_title = current_article.get('title', '').strip()
        
        if prev_title != curr_title:
            self.logger.debug(f"Title change detected for {current_article['id']}")
            return True
        
        # No changes detected
        return False
    
    def _parse_date(self, date_str: str) -> datetime:
        if isinstance(date_str, datetime):
            return date_str

        try:
            # Simple ISO format parsing
            if date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(date_str)
        except Exception:
            # Fallback - just return current time
            return datetime.now(timezone.utc)
    
    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute SHA256 hash of article content.
        
        Args:
            content: Article content to hash
            
        Returns:
            Hexadecimal hash string
        """
        # Normalize content for consistent hashing
        normalized_content = content.strip().replace('\r\n', '\n').replace('\r', '\n')
        
        # Compute SHA256 hash
        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    def generate_change_summary(self, changes: Dict[str, Set[str]], current_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a detailed summary of detected changes.
        
        Args:
            changes: Change detection results
            current_articles: Current article data
            
        Returns:
            Detailed change summary
        """
        current_lookup = {article['id']: article for article in current_articles}
        
        summary = {
            'total_articles': len(current_articles),
            'added_count': len(changes['added']),
            'updated_count': len(changes['updated']),
            'unchanged_count': len(changes['unchanged']),
            'removed_count': len(changes['removed']),
            'change_percentage': 0.0,
            'added_articles': [],
            'updated_articles': [],
            'removed_articles': list(changes['removed'])
        }
        
        # Calculate change percentage
        total_changes = summary['added_count'] + summary['updated_count']
        if summary['total_articles'] > 0:
            summary['change_percentage'] = (total_changes / summary['total_articles']) * 100
        
        # Add details for added articles
        for article_id in list(changes['added'])[:10]:  # Limit to first 10
            if article_id in current_lookup:
                article = current_lookup[article_id]
                summary['added_articles'].append({
                    'id': article_id,
                    'title': article.get('title', 'Unknown'),
                    'url': article.get('url', '')
                })
        
        # Add details for updated articles
        for article_id in list(changes['updated'])[:10]:  # Limit to first 10
            if article_id in current_lookup:
                article = current_lookup[article_id]
                summary['updated_articles'].append({
                    'id': article_id,
                    'title': article.get('title', 'Unknown'),
                    'url': article.get('url', '')
                })
        
        return summary
