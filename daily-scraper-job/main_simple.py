#!/usr/bin/env python3

# Simplified daily scraper for testing

import os
import sys
import argparse
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "config"))

def main():
    parser = argparse.ArgumentParser(description="Daily OptiSigns scraper job")
    parser.add_argument('--dry-run', action='store_true', help='Test mode')
    parser.add_argument('--max-articles', type=int, help='Limit articles')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    print("🚀 Starting simplified daily scraper job")
    print(f"Dry run: {args.dry_run}")
    print(f"Max articles: {args.max_articles}")
    
    # Test basic imports
    try:
        from config.settings import Settings
        print("✅ Settings imported")
        
        settings = Settings()
        if args.dry_run:
            settings.dry_run = True
        if args.max_articles:
            settings.max_articles = args.max_articles
            
        print(f"✅ Settings configured - dry_run: {settings.dry_run}")
        
    except Exception as e:
        print(f"❌ Settings failed: {e}")
        return
    
    # Test scraper
    try:
        from src.scraper import EnhancedScraper
        print("✅ Scraper imported")
        
        scraper = EnhancedScraper(settings)
        print("✅ Scraper created")
        
        # Test URL discovery
        print("🔍 Testing URL discovery...")
        urls = scraper._discover_article_urls()
        print(f"✅ Found {len(urls)} URLs")
        
        if settings.max_articles:
            urls = urls[:settings.max_articles]
            print(f"✅ Limited to {len(urls)} URLs")
        
        # Test scraping one article
        if urls:
            print(f"📖 Testing scrape of: {urls[0]}")
            article = scraper._scrape_article(urls[0])
            if article:
                print(f"✅ Scraped: {article['title'][:50]}...")
                print(f"   Content: {len(article['content'])} chars")
                print(f"   Hash: {article['content_hash'][:8]}...")
            else:
                print("❌ Failed to scrape article")
        
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test delta detection
    try:
        from src.delta_detector import DeltaDetector
        print("✅ Delta detector imported")
        
        detector = DeltaDetector(settings)
        print("✅ Delta detector created")
        
    except Exception as e:
        print(f"❌ Delta detector failed: {e}")
        return
    
    # Test storage
    try:
        from src.storage import StateManager
        print("✅ Storage imported")
        
        storage = StateManager(settings)
        print("✅ Storage created")
        
        # Test loading state
        state = storage.load_state()
        print(f"✅ State loaded: {len(state.get('articles', {}))} previous articles")
        
    except Exception as e:
        print(f"❌ Storage failed: {e}")
        return
    
    print("🎉 All basic tests passed!")
    print("You can now try: python main.py --dry-run --max-articles 3")

if __name__ == '__main__':
    main()
