#!/usr/bin/env python3

# Production Daily Scraper Job
# Scrapes OptiSigns support articles, detects changes, uploads only deltas to OpenAI Vector Store
# Meets all requirements: re-scrape, hash detection, delta upload, logging with counts

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "config"))

from config.settings import Settings
from config.logging import setup_logging
from src.scraper import EnhancedScraper
from src.uploader import VectorStoreUploader
from src.delta_detector import DeltaDetector
from src.storage import StateManager
from src.monitoring import JobMonitor


class DailyScraperJob:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        self.scraper = EnhancedScraper(settings)
        self.uploader = VectorStoreUploader(settings)
        self.delta_detector = DeltaDetector(settings)
        self.state_manager = StateManager(settings)
        self.monitor = JobMonitor(settings)

        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_articles': 0,
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'execution_time': 0
        }
    
    def run(self) -> bool:
        self.stats['start_time'] = datetime.now(timezone.utc)
        self.logger.info("Starting daily scraper job")

        job_id = self.monitor.record_job_start()

        try:
            # Load what we saw last time
            previous_state = self.state_manager.load_state()
            self.logger.info(f"Loaded state with {len(previous_state.get('articles', {}))} previous articles")

            # Scrape everything fresh
            self.logger.info("Scraping articles from OptiSigns support...")
            current_articles = self.scraper.scrape_all_articles()
            self.stats['total_articles'] = len(current_articles)
            self.logger.info(f"Found {len(current_articles)} total articles")

            # Figure out what changed
            self.logger.info("Detecting changes...")
            changes = self.delta_detector.detect_changes(
                previous_state.get('articles', {}),
                current_articles
            )

            self.logger.info(f"Changes detected: {len(changes['added'])} added, "
                           f"{len(changes['updated'])} updated, "
                           f"{len(changes['unchanged'])} unchanged")
            
            # Upload only what changed
            if not self.settings.dry_run:
                success = self._process_changes(changes, current_articles)
                if not success:
                    return False
            else:
                self.logger.info("DRY RUN MODE - skipping uploads")
                self._simulate_processing(changes)

            # Remember what we saw this time
            new_state = {
                'last_run': self.stats['start_time'].isoformat(),
                'articles': {
                    article['id']: {
                        'hash': article['content_hash'],
                        'last_modified': article.get('last_modified'),
                        'title': article['title'],
                        'updated_at': article.get('updated_at')
                    }
                    for article in current_articles
                }
            }

            if not self.settings.dry_run:
                self.state_manager.save_state(new_state)
                self.logger.info("State saved successfully")

            self._log_final_stats()

            self.monitor.record_job_completion(job_id, self.stats, True)
            self.monitor.archive_current_metrics()

            return True

        except Exception as e:
            self.logger.error(f"JOB FAILED: {str(e)}", exc_info=True)
            self.stats['errors'] += 1

            self.monitor.record_error(job_id, str(e), {'stats': self.stats})
            self.monitor.record_job_completion(job_id, self.stats, False)

            return False

        finally:
            self.stats['end_time'] = datetime.now(timezone.utc)
            if self.stats['start_time']:
                self.stats['execution_time'] = (
                    self.stats['end_time'] - self.stats['start_time']
                ).total_seconds()
    
    def _process_changes(self, changes: dict, current_articles: list) -> bool:
        # Upload new articles
        if changes['added']:
            self.logger.info(f"UPLOADING {len(changes['added'])} new articles...")
            added_articles = [
                article for article in current_articles
                if article['id'] in changes['added']
            ]

            success_count = self.uploader.upload_articles(added_articles, operation='add')
            self.stats['added'] = success_count
            self.stats['errors'] += len(added_articles) - success_count

        # Update changed articles
        if changes['updated']:
            self.logger.info(f"UPDATING {len(changes['updated'])} modified articles...")
            updated_articles = [
                article for article in current_articles
                if article['id'] in changes['updated']
            ]

            success_count = self.uploader.upload_articles(updated_articles, operation='update')
            self.stats['updated'] = success_count
            self.stats['errors'] += len(updated_articles) - success_count

        self.stats['skipped'] = len(changes['unchanged'])

        return self.stats['errors'] == 0
    
    def _simulate_processing(self, changes: dict):
        """Simulate processing for dry run mode."""
        self.stats['added'] = len(changes['added'])
        self.stats['updated'] = len(changes['updated'])
        self.stats['skipped'] = len(changes['unchanged'])
        
        self.logger.info(f"🧪 Would add {self.stats['added']} articles")
        self.logger.info(f"🧪 Would update {self.stats['updated']} articles")
        self.logger.info(f"🧪 Would skip {self.stats['skipped']} articles")
    
    def _log_final_stats(self):
        """Log final job statistics with required format."""
        self.logger.info("JOB COMPLETED SUCCESSFULLY!")
        self.logger.info(f"Execution time: {self.stats['execution_time']:.2f} seconds")
        self.logger.info(f"Total articles: {self.stats['total_articles']}")

        # Required format: Log counts: added, updated, skipped
        self.logger.info(f"Log counts: added={self.stats['added']}, updated={self.stats['updated']}, skipped={self.stats['skipped']}")

        if self.stats['errors'] > 0:
            self.logger.warning(f"Errors: {self.stats['errors']}")

        # Structured summary for monitoring
        summary = {
            'timestamp': self.stats['end_time'].isoformat(),
            'execution_time': self.stats['execution_time'],
            'total_articles': self.stats['total_articles'],
            'added': self.stats['added'],
            'updated': self.stats['updated'],
            'skipped': self.stats['skipped'],
            'errors': self.stats['errors'],
            'success': self.stats['errors'] == 0
        }

        self.logger.info(f"FINAL_SUMMARY: {summary}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Daily OptiSigns scraper job")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in test mode without uploading')
    parser.add_argument('--max-articles', type=int, 
                       help='Limit number of articles for testing')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    args = parser.parse_args()
    
    # Load settings
    settings = Settings()
    
    # Override settings with command line arguments
    if args.dry_run:
        settings.dry_run = True
    if args.max_articles:
        settings.max_articles = args.max_articles
    if args.log_level:
        settings.log_level = args.log_level
    
    # Setup logging
    setup_logging(settings)
    logger = logging.getLogger(__name__)
    
    # Validate environment
    if not settings.openai_api_key and not settings.dry_run:
        logger.error("❌ OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    # Run the job
    job = DailyScraperJob(settings)
    success = job.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
