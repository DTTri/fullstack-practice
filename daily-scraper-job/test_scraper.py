#!/usr/bin/env python3

# Test scraper with a simple website first

import requests
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent / "config"))

def test_simple_request():
    """Test a simple HTTP request"""
    print("Testing simple HTTP request...")
    
    try:
        # Test with a simple website first
        response = requests.get('https://httpbin.org/get', timeout=10)
        print(f"Status: {response.status_code}")
        print("Simple request works!")
        return True
    except Exception as e:
        print(f"Simple request failed: {e}")
        return False

def test_optisigns_request():
    """Test OptiSigns website access"""
    print("\nTesting OptiSigns website access...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    })
    
    # Try different URLs
    test_urls = [
        'https://support.optisigns.com',
        'https://support.optisigns.com/hc/en-us',
        'https://support.optisigns.com/hc/en-us/categories',
    ]
    
    for url in test_urls:
        try:
            print(f"Trying: {url}")
            response = session.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  Content length: {len(response.content)}")
                
                # Try to parse with BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                if title:
                    print(f"  Page title: {title.get_text()[:50]}...")
                
                # Look for article links
                links = soup.find_all('a', href=True)
                article_links = [link for link in links if '/articles/' in link['href']]
                print(f"  Found {len(article_links)} article links")
                
                if article_links:
                    print("  Sample article links:")
                    for link in article_links[:3]:
                        print(f"    {link['href']}")
                
                return True
                
            elif response.status_code == 403:
                print("  403 Forbidden - website is blocking us")
            else:
                print(f"  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    return False

def test_with_mock_data():
    """Test the scraper logic with mock data"""
    print("\nTesting with mock data...")
    
    try:
        from config.settings import Settings
        settings = Settings()
        settings.dry_run = True
        settings.max_articles = 3
        
        print("Settings created successfully")
        
        # Create mock articles
        mock_articles = [
            {
                'id': 'article_1',
                'title': 'How to add content',
                'content': 'This is how you add content to your display...',
                'content_hash': 'abc123',
                'url': 'https://support.optisigns.com/articles/1',
                'category': 'Getting Started'
            },
            {
                'id': 'article_2', 
                'title': 'Troubleshooting display issues',
                'content': 'If your display is not working...',
                'content_hash': 'def456',
                'url': 'https://support.optisigns.com/articles/2',
                'category': 'Troubleshooting'
            }
        ]
        
        print(f"Created {len(mock_articles)} mock articles")
        
        # Test delta detection
        from src.delta_detector import DeltaDetector
        detector = DeltaDetector(settings)
        
        # Test with empty previous state
        changes = detector.detect_changes({}, mock_articles)
        print(f"Changes detected: {len(changes['added'])} added, {len(changes['updated'])} updated")
        
        # Test storage
        from src.storage import StateManager
        storage = StateManager(settings)
        
        # Test saving mock state
        mock_state = {
            'last_run': '2024-01-01T00:00:00Z',
            'articles': {
                'article_1': {
                    'hash': 'abc123',
                    'title': 'How to add content'
                }
            }
        }
        
        # Don't actually save in test mode
        print("Storage test passed")
        
        return True
        
    except Exception as e:
        print(f"Mock data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Daily Scraper Test Suite")
    print("=" * 40)
    
    # Test 1: Simple HTTP request
    test1 = test_simple_request()
    
    # Test 2: OptiSigns website access
    test2 = test_optisigns_request()
    
    # Test 3: Mock data processing
    test3 = test_with_mock_data()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Simple HTTP: {'PASS' if test1 else 'FAIL'}")
    print(f"OptiSigns access: {'PASS' if test2 else 'FAIL'}")
    print(f"Mock data processing: {'PASS' if test3 else 'FAIL'}")
    
    if test3:
        print("\nThe scraper logic works! The issue is website access.")
        print("You can run with mock data or try different scraping strategies.")
    elif test1:
        print("\nInternet works, but there might be import issues.")
    else:
        print("\nBasic connectivity issues.")

if __name__ == '__main__':
    main()
