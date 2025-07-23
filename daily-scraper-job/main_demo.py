#!/usr/bin/env python3

# Demo version using existing scraped data

import os
import sys
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Add paths
sys.path.append(str(Path(__file__).parent / "src"))
sys.path.append(str(Path(__file__).parent / "config"))

def load_existing_articles():
    """Load articles from the existing scraped data"""
    
    # Look for existing scraped data
    possible_paths = [
        Path("../normalizeWebContent/output"),
        Path("../web-scraper/output"), 
        Path("../optibot-assistant/data"),
        Path("./demo_data")
    ]
    
    articles = []
    
    for data_path in possible_paths:
        if data_path.exists():
            print(f"Found data directory: {data_path}")
            
            # Look for markdown files
            md_files = list(data_path.glob("*.md"))
            if md_files:
                print(f"Found {len(md_files)} markdown files")
                
                for md_file in md_files:
                    if md_file.name == "INDEX.md":
                        continue
                        
                    try:
                        content = md_file.read_text(encoding='utf-8')
                        
                        # Extract title from first line or filename
                        lines = content.split('\n')
                        title = lines[0].replace('#', '').strip() if lines else md_file.stem
                        
                        # Create article object
                        article = {
                            'id': f"article_{md_file.stem}",
                            'title': title,
                            'content': content,
                            'content_hash': hashlib.sha256(content.encode()).hexdigest(),
                            'url': f"https://support.optisigns.com/articles/{md_file.stem}",
                            'scraped_at': datetime.now(timezone.utc).isoformat(),
                            'category': 'Support',
                            'word_count': len(content.split()),
                            'char_count': len(content)
                        }
                        
                        articles.append(article)
                        
                    except Exception as e:
                        print(f"Error reading {md_file}: {e}")
                
                break  # Use first directory found
    
    if not articles:
        # Create demo articles if no existing data found
        print("No existing data found, creating demo articles...")
        articles = create_demo_articles()
    
    return articles

def create_demo_articles():
    """Create demo articles for testing"""
    demo_articles = [
        {
            'id': 'article_youtube_video',
            'title': 'How to Add a YouTube Video',
            'content': '''# How to Add a YouTube Video

To add a YouTube video to your OptiSigns display:

## Steps
1. Go to Files/Assets and click "Add Content"
2. Select "YouTube" from the content options  
3. Paste the YouTube video URL or video ID
4. Configure playback settings (autoplay, loop, etc.)
5. Assign the video to your screen or playlist

## Tips
- Make sure the video is public or unlisted
- Test the video before deploying to screens
- Consider video length for your display schedule

For more help, contact support.''',
            'url': 'https://support.optisigns.com/articles/youtube-video',
            'category': 'Content Management',
            'scraped_at': datetime.now(timezone.utc).isoformat(),
        },
        {
            'id': 'article_playlist_setup', 
            'title': 'Setting Up Playlists',
            'content': '''# Setting Up Playlists

Playlists allow you to organize and schedule your content effectively.

## Creating a Playlist
1. Navigate to Playlists in your dashboard
2. Click "Create New Playlist"
3. Add content items from your library
4. Set duration for each item
5. Configure transition effects

## Best Practices
- Keep playlists focused on specific themes
- Test playlist timing before deployment
- Use appropriate content for your audience

Contact support for advanced playlist features.''',
            'url': 'https://support.optisigns.com/articles/playlist-setup',
            'category': 'Content Management', 
            'scraped_at': datetime.now(timezone.utc).isoformat(),
        },
        {
            'id': 'article_troubleshooting',
            'title': 'Display Troubleshooting Guide',
            'content': '''# Display Troubleshooting Guide

Common issues and solutions for OptiSigns displays.

## Display Not Showing Content
1. Check internet connection
2. Verify screen is powered on
3. Check OptiSigns app is running
4. Restart the display device

## Content Not Updating
1. Check content schedule
2. Verify internet connectivity
3. Force refresh from dashboard
4. Check device storage space

## Performance Issues
- Close unnecessary applications
- Check device specifications
- Monitor network bandwidth
- Update OptiSigns app

For technical support, contact our team.''',
            'url': 'https://support.optisigns.com/articles/troubleshooting',
            'category': 'Troubleshooting',
            'scraped_at': datetime.now(timezone.utc).isoformat(),
        }
    ]
    
    # Add content hash to each article
    for article in demo_articles:
        article['content_hash'] = hashlib.sha256(article['content'].encode()).hexdigest()
        article['word_count'] = len(article['content'].split())
        article['char_count'] = len(article['content'])
    
    return demo_articles

def simulate_changes(articles, change_type="add_new"):
    """Simulate different types of changes for demo"""
    
    if change_type == "add_new":
        # Add a new article
        new_article = {
            'id': 'article_new_feature',
            'title': 'New Feature: Advanced Scheduling',
            'content': '''# New Feature: Advanced Scheduling

We've added advanced scheduling capabilities to OptiSigns.

## What's New
- Hourly content scheduling
- Day-specific playlists  
- Holiday scheduling
- Automatic content rotation

## How to Use
1. Go to Schedule in your dashboard
2. Select "Advanced Scheduling"
3. Configure your time-based rules
4. Apply to your displays

This feature is available on Pro plans and above.''',
            'url': 'https://support.optisigns.com/articles/advanced-scheduling',
            'category': 'New Features',
            'scraped_at': datetime.now(timezone.utc).isoformat(),
        }
        new_article['content_hash'] = hashlib.sha256(new_article['content'].encode()).hexdigest()
        new_article['word_count'] = len(new_article['content'].split())
        new_article['char_count'] = len(new_article['content'])
        
        articles.append(new_article)
        print("Simulated: Added 1 new article")
    
    elif change_type == "update_existing":
        # Update an existing article
        if articles:
            article = articles[0]
            article['content'] += "\n\n## Updated Information\nThis article was recently updated with new information."
            article['content_hash'] = hashlib.sha256(article['content'].encode()).hexdigest()
            article['word_count'] = len(article['content'].split())
            article['char_count'] = len(article['content'])
            print("Simulated: Updated 1 existing article")
    
    return articles

def main():
    parser = argparse.ArgumentParser(description="Daily OptiSigns scraper demo")
    parser.add_argument('--dry-run', action='store_true', help='Test mode')
    parser.add_argument('--max-articles', type=int, help='Limit articles')
    parser.add_argument('--simulate', choices=['add_new', 'update_existing', 'no_changes'], 
                       default='add_new', help='Simulate different change types')
    
    args = parser.parse_args()
    
    print("Daily Scraper Job - Demo Mode")
    print("=" * 40)
    print(f"Dry run: {args.dry_run}")
    print(f"Max articles: {args.max_articles}")
    print(f"Simulation: {args.simulate}")
    print()
    
    try:
        # Load settings
        from config.settings import Settings
        settings = Settings()
        if args.dry_run:
            settings.dry_run = True
        if args.max_articles:
            settings.max_articles = args.max_articles
        
        # Load existing articles (simulating scraping)
        print("Loading existing articles...")
        current_articles = load_existing_articles()
        
        if args.max_articles:
            current_articles = current_articles[:args.max_articles]
        
        print(f"Loaded {len(current_articles)} articles")
        
        # Simulate changes
        if args.simulate != 'no_changes':
            current_articles = simulate_changes(current_articles, args.simulate)
        
        # Load previous state
        from src.storage import StateManager
        storage = StateManager(settings)
        previous_state = storage.load_state()
        
        print(f"Previous state: {len(previous_state.get('articles', {}))} articles")
        
        # Detect changes
        from src.delta_detector import DeltaDetector
        detector = DeltaDetector(settings)
        
        changes = detector.detect_changes(
            previous_state.get('articles', {}),
            current_articles
        )
        
        print(f"Changes detected:")
        print(f"  Added: {len(changes['added'])}")
        print(f"  Updated: {len(changes['updated'])}")
        print(f"  Unchanged: {len(changes['unchanged'])}")
        
        # Show what would be uploaded
        if changes['added']:
            print(f"\nWould upload {len(changes['added'])} new articles:")
            for article_id in list(changes['added'])[:3]:
                article = next(a for a in current_articles if a['id'] == article_id)
                print(f"  - {article['title']}")
        
        if changes['updated']:
            print(f"\nWould update {len(changes['updated'])} articles:")
            for article_id in list(changes['updated'])[:3]:
                article = next(a for a in current_articles if a['id'] == article_id)
                print(f"  - {article['title']}")
        
        # Save new state (if not dry run)
        if not settings.dry_run:
            new_state = {
                'last_run': datetime.now(timezone.utc).isoformat(),
                'articles': {
                    article['id']: {
                        'hash': article['content_hash'],
                        'title': article['title'],
                        'last_modified': article.get('last_modified'),
                        'updated_at': article.get('updated_at')
                    }
                    for article in current_articles
                }
            }
            storage.save_state(new_state)
            print("\nState saved successfully")
        else:
            print("\nDry run - state not saved")
        
        print("\nDemo completed successfully!")
        print("\nThis demonstrates how the daily scraper would work:")
        print("1. Load current articles (normally by scraping)")
        print("2. Compare with previous state")
        print("3. Detect only what changed")
        print("4. Upload only the changes to OpenAI")
        print("5. Save new state for next run")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
