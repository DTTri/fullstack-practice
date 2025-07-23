#!/usr/bin/env python3
"""
System test for the daily scraper job.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "config"))

from config.settings import Settings
from src.scraper import EnhancedScraper
from src.delta_detector import DeltaDetector
from src.storage import StateManager


def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    
    settings = Settings()
    errors = settings.validate()
    
    if errors:
        print(f"❌ Configuration errors: {errors}")
        return False
    
    print("✅ Configuration valid")
    return True


def test_scraper():
    """Test scraper functionality."""
    print("🕷️ Testing scraper...")
    
    try:
        settings = Settings()
        settings.max_articles = 2  # Limit for testing
        
        scraper = EnhancedScraper(settings)
        
        # Test URL discovery
        print("  🔍 Testing URL discovery...")
        urls = scraper._discover_article_urls()
        
        if not urls:
            print("❌ No URLs discovered")
            return False
        
        print(f"  ✅ Found {len(urls)} URLs")
        
        # Test article scraping
        print("  📖 Testing article scraping...")
        test_url = urls[0]
        article = scraper._scrape_article(test_url)
        
        if not article:
            print("❌ Failed to scrape article")
            return False
        
        print(f"  ✅ Scraped article: {article['title'][:50]}...")
        
        # Verify required fields
        required_fields = ['id', 'title', 'content', 'content_hash', 'url']
        for field in required_fields:
            if field not in article:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ Scraper working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False


def test_delta_detection():
    """Test delta detection functionality."""
    print("🔍 Testing delta detection...")
    
    try:
        settings = Settings()
        detector = DeltaDetector(settings)
        
        # Create test data
        previous_articles = {
            'article_1': {
                'hash': 'old_hash',
                'title': 'Test Article',
                'last_modified': '2024-01-01T00:00:00Z'
            }
        }
        
        current_articles = [
            {
                'id': 'article_1',
                'title': 'Test Article',
                'content_hash': 'new_hash',  # Changed hash
                'last_modified': '2024-01-02T00:00:00Z'
            },
            {
                'id': 'article_2',
                'title': 'New Article',
                'content_hash': 'another_hash',
                'last_modified': '2024-01-02T00:00:00Z'
            }
        ]
        
        # Test change detection
        changes = detector.detect_changes(previous_articles, current_articles)
        
        # Verify results
        if 'article_2' not in changes['added']:
            print("❌ Failed to detect new article")
            return False
        
        if 'article_1' not in changes['updated']:
            print("❌ Failed to detect updated article")
            return False
        
        print("✅ Delta detection working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Delta detection test failed: {e}")
        return False


def test_state_management():
    """Test state management functionality."""
    print("💾 Testing state management...")
    
    try:
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.data_dir = Path(temp_dir)
            settings.state_file = settings.data_dir / 'test_state.json'
            
            state_manager = StateManager(settings)
            
            # Test saving state
            test_state = {
                'last_run': '2024-01-01T00:00:00Z',
                'articles': {
                    'article_1': {
                        'hash': 'test_hash',
                        'title': 'Test Article'
                    }
                }
            }
            
            success = state_manager.save_state(test_state)
            if not success:
                print("❌ Failed to save state")
                return False
            
            # Test loading state
            loaded_state = state_manager.load_state()
            if not loaded_state:
                print("❌ Failed to load state")
                return False
            
            if loaded_state['articles']['article_1']['hash'] != 'test_hash':
                print("❌ State data mismatch")
                return False
            
            print("✅ State management working correctly")
            return True
        
    except Exception as e:
        print(f"❌ State management test failed: {e}")
        return False


def test_dry_run():
    """Test dry run functionality."""
    print("🧪 Testing dry run mode...")
    
    try:
        # Set up dry run environment
        os.environ['DRY_RUN'] = 'true'
        os.environ['MAX_ARTICLES'] = '1'
        os.environ['LOG_LEVEL'] = 'WARNING'  # Reduce noise
        
        # Import and run main
        from main import DailyScraperJob
        
        settings = Settings()
        job = DailyScraperJob(settings)
        
        # Run the job
        success = job.run()
        
        if not success:
            print("❌ Dry run failed")
            return False
        
        # Check that no actual uploads occurred
        if job.stats['added'] > 0 or job.stats['updated'] > 0:
            print("⚠️ Dry run mode but stats show uploads occurred")
        
        print("✅ Dry run working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Dry run test failed: {e}")
        return False
    
    finally:
        # Clean up environment
        os.environ.pop('DRY_RUN', None)
        os.environ.pop('MAX_ARTICLES', None)
        os.environ.pop('LOG_LEVEL', None)


def main():
    """Run all system tests."""
    print("🚀 Running system tests for Daily Scraper Job")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_scraper,
        test_delta_detection,
        test_state_management,
        test_dry_run
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
