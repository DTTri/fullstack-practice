#!/usr/bin/env python3

# Simple health check script for Docker
# Returns 0 if healthy, 1 if unhealthy

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['OPENAI_API_KEY']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    return len(missing) == 0, missing

def check_dependencies():
    """Check if required Python packages are available."""
    required_packages = ['requests', 'openai', 'bs4']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing

def check_last_run():
    """Check when the job last ran successfully."""
    state_file = Path('state/job_state.json')
    
    if not state_file.exists():
        return True, "No previous run found (first run)"
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        last_run = state.get('last_run')
        if not last_run:
            return True, "No last_run timestamp found (first run)"
        
        last_run_time = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Job should run daily, so warn if it's been more than 25 hours
        if now - last_run_time > timedelta(hours=25):
            return False, f"Last run was {now - last_run_time} ago"
        
        return True, f"Last run: {last_run_time}"
        
    except Exception as e:
        return False, f"Error reading state: {e}"

def main():
    """Main health check function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--verbose':
        verbose = True
        print("Daily Scraper Health Check")
        print("=" * 30)
    else:
        verbose = False
    
    checks = [
        ("Environment Variables", check_environment),
        ("Dependencies", check_dependencies),
        ("Last Run", check_last_run),
    ]
    
    all_healthy = True
    
    for check_name, check_func in checks:
        try:
            healthy, message = check_func()
            
            if verbose:
                status = "PASS" if healthy else "FAIL"
                print(f"{check_name}: {status} - {message}")
            
            if not healthy:
                all_healthy = False
                
        except Exception as e:
            if verbose:
                print(f"{check_name}: ERROR - {e}")
            all_healthy = False
    
    if verbose:
        print("=" * 30)
        if all_healthy:
            print("Overall Status: HEALTHY")
        else:
            print("Overall Status: UNHEALTHY")
    
    # Return appropriate exit code
    sys.exit(0 if all_healthy else 1)

if __name__ == '__main__':
    main()
