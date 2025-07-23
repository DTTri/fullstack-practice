#!/usr/bin/env python3

# Script to view and serve job logs
# Provides link to job logs as required

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import http.server
import socketserver
import threading
import webbrowser

def find_latest_log():
    """Find the most recent log file."""
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        return None
    
    log_files = list(logs_dir.glob('*.log'))
    if not log_files:
        return None
    
    # Sort by modification time, newest first
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return log_files[0]

def show_last_run_summary():
    """Show summary of the last run."""
    state_file = Path('state/job_state.json')
    
    if not state_file.exists():
        print("No previous run found")
        return
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        print("LAST RUN SUMMARY")
        print("=" * 40)
        print(f"Last run: {state.get('last_run', 'Unknown')}")
        print(f"Total articles: {len(state.get('articles', {}))}")
        
        # Look for the latest log file
        latest_log = find_latest_log()
        if latest_log:
            print(f"Latest log: {latest_log.name}")
            print(f"Log size: {latest_log.stat().st_size} bytes")
            print(f"Log modified: {datetime.fromtimestamp(latest_log.stat().st_mtime)}")
            
            # Try to extract counts from log
            try:
                with open(latest_log, 'r') as f:
                    content = f.read()
                    
                # Look for the required log format: "Log counts: added=X, updated=Y, skipped=Z"
                for line in content.split('\n'):
                    if 'Log counts:' in line:
                        print(f"Counts: {line.split('Log counts:')[1].strip()}")
                        break
                        
            except Exception as e:
                print(f"Error reading log: {e}")
        
    except Exception as e:
        print(f"Error reading state: {e}")

def serve_logs(port=8080):
    """Serve logs via HTTP server."""
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print("No logs directory found")
        return
    
    class LogHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(logs_dir), **kwargs)
        
        def do_GET(self):
            if self.path == '/':
                # Generate index page
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Daily Scraper Job Logs</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .log-entry { margin: 10px 0; padding: 10px; background: #f5f5f5; }
                        .timestamp { color: #666; font-size: 0.9em; }
                    </style>
                </head>
                <body>
                    <h1>Daily Scraper Job Logs</h1>
                    <h2>Available Log Files:</h2>
                    <ul>
                """
                
                # List log files
                for log_file in sorted(logs_dir.glob('*.log'), key=lambda f: f.stat().st_mtime, reverse=True):
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    size = log_file.stat().st_size
                    html += f'<li><a href="/{log_file.name}">{log_file.name}</a> ({size} bytes, {mtime})</li>'
                
                html += """
                    </ul>
                    <h2>Last Run Artifact:</h2>
                    <div class="log-entry">
                """
                
                # Add last run info
                state_file = Path('../state/job_state.json')
                if state_file.exists():
                    try:
                        with open(state_file, 'r') as f:
                            state = json.load(f)
                        html += f"<p><strong>Last run:</strong> {state.get('last_run', 'Unknown')}</p>"
                        html += f"<p><strong>Total articles:</strong> {len(state.get('articles', {}))}</p>"
                    except:
                        html += "<p>Error reading state file</p>"
                else:
                    html += "<p>No state file found</p>"
                
                html += """
                    </div>
                    <p><em>This page provides access to job logs and last run artifacts as required.</em></p>
                </body>
                </html>
                """
                
                self.wfile.write(html.encode())
            else:
                super().do_GET()
    
    try:
        with socketserver.TCPServer(("", port), LogHandler) as httpd:
            print(f"Serving logs at http://localhost:{port}")
            print("Press Ctrl+C to stop")
            
            # Try to open browser
            try:
                webbrowser.open(f'http://localhost:{port}')
            except:
                pass
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping log server")
    except Exception as e:
        print(f"Error starting server: {e}")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'summary':
            show_last_run_summary()
        elif command == 'serve':
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            serve_logs(port)
        elif command == 'latest':
            latest_log = find_latest_log()
            if latest_log:
                print(f"Latest log: {latest_log}")
                with open(latest_log, 'r') as f:
                    print(f.read())
            else:
                print("No log files found")
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("Daily Scraper Job Log Viewer")
        print("=" * 40)
        print("Usage:")
        print("  python view-logs.py summary    - Show last run summary")
        print("  python view-logs.py latest     - Show latest log content")
        print("  python view-logs.py serve      - Start HTTP server for logs")
        print("  python view-logs.py serve 9000 - Start server on port 9000")
        print()
        
        # Show quick summary
        show_last_run_summary()

if __name__ == '__main__':
    main()
