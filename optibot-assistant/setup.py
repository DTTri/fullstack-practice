#!/usr/bin/env python3
"""
Setup script for OptiBot Assistant environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install Python requirements."""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        sys.exit(1)

def check_openai_key():
    """Check if OpenAI API key is set."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return False
    else:
        print("OpenAI API key found")
        return True

def create_directories():
    """Create necessary directories."""
    dirs = ['logs', 'screenshots']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"Created directory: {dir_name}")

def main():
    """Main setup function."""
    print("Setting up OptiBot Assistant environment...")
    
    create_directories()
    install_requirements()
    
    if check_openai_key():
        print("\nSetup complete! You can now run:")
        print("python upload_to_openai.py --input ../normalizeWebContent/output")
    else:
        print("\nSetup incomplete. Please set your OpenAI API key first.")

if __name__ == '__main__':
    main()
