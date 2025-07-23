#!/usr/bin/env python3

# Simple test to check what's working

import os
import sys
from pathlib import Path

print("🔍 Testing imports...")

try:
    print("✅ Basic imports work")
    
    # Test config
    sys.path.append(str(Path(__file__).parent / "config"))
    from config.settings import Settings
    print("✅ Settings import works")
    
    # Test settings creation
    settings = Settings()
    print(f"✅ Settings created - dry_run: {settings.dry_run}")
    
    # Test src imports one by one
    sys.path.append(str(Path(__file__).parent / "src"))
    
    try:
        from src.delta_detector import DeltaDetector
        print("✅ DeltaDetector import works")
    except Exception as e:
        print(f"❌ DeltaDetector import failed: {e}")
    
    try:
        from src.storage import StateManager
        print("✅ StateManager import works")
    except Exception as e:
        print(f"❌ StateManager import failed: {e}")
    
    try:
        from src.monitoring import JobMonitor
        print("✅ JobMonitor import works")
    except Exception as e:
        print(f"❌ JobMonitor import failed: {e}")
    
    try:
        from src.scraper import EnhancedScraper
        print("✅ EnhancedScraper import works")
    except Exception as e:
        print(f"❌ EnhancedScraper import failed: {e}")
    
    try:
        from src.uploader import VectorStoreUploader
        print("✅ VectorStoreUploader import works")
    except Exception as e:
        print(f"❌ VectorStoreUploader import failed: {e}")

except Exception as e:
    print(f"❌ Import test failed: {e}")

print("\n🚀 If all imports work, try running main.py again")
