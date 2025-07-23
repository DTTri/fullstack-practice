#!/usr/bin/env python3
"""
Validation script to check if everything is ready for OptiBot setup.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def check_api_key():
    """Check if OpenAI API key is set."""
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        # Mask the key for security
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        return True, f"Set ({masked_key})"
    return False, "Not set"

def check_input_files():
    """Check if input markdown files exist."""
    input_dir = Path("../normalizeWebContent/output")
    
    if not input_dir.exists():
        return False, "Directory not found", 0
    
    markdown_files = [f for f in input_dir.glob("*.md") if f.name != "INDEX.md"]
    return True, f"Found {len(markdown_files)} files", len(markdown_files)

def check_dependencies():
    """Check if required Python packages are installed."""
    required_packages = ['openai', 'rich', 'click', 'yaml', 'pathlib2']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, "All installed"

def check_directories():
    """Check if required directories exist."""
    dirs = ['logs', 'screenshots', 'utils']
    missing = []
    
    for dir_name in dirs:
        if not Path(dir_name).exists():
            missing.append(dir_name)
    
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, "All exist"

def main():
    """Main validation function."""
    console.print("[bold blue]OptiBot Setup Validation[/bold blue]")
    
    table = Table(title="Setup Checklist")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    api_ok, api_details = check_api_key()
    table.add_row(
        "OpenAI API Key",
        "Ready" if api_ok else "Missing",
        api_details
    )
    
    deps_ok, deps_details = check_dependencies()
    table.add_row(
        "Python Dependencies",
        "Ready" if deps_ok else "Missing",
        deps_details
    )
    
    dirs_ok, dirs_details = check_directories()
    table.add_row(
        "Required Directories",
        "Ready" if dirs_ok else "Missing",
        dirs_details
    )
    
    files_ok, files_details, file_count = check_input_files()
    table.add_row(
        "Input Markdown Files",
        "Ready" if files_ok else "Missing",
        files_details
    )
    
    console.print(table)
    
    all_ready = api_ok and deps_ok and dirs_ok and files_ok
    
    if all_ready:
        console.print("\n[bold green]All checks passed! Ready to proceed.[/bold green]")
        
        next_steps = """
[bold]Next Steps:[/bold]

1. Run the upload script:
   [cyan]python upload_to_openai.py --input ../normalizeWebContent/output[/cyan]

2. Create assistant in OpenAI Playground:
   [cyan]https://platform.openai.com/playground/assistants[/cyan]

3. Test with query: [cyan]"How do I add a YouTube video?"[/cyan]

4. Take screenshot showing response with citations
        """
        
        console.print(Panel(next_steps, title="🚀 Ready to Go!", border_style="green"))
        
        # Show estimated upload stats
        if file_count > 0:
            estimated_chunks = int(file_count * 1.66)  # Based on test results
            console.print(f"\n[blue]📊 Estimated upload: {file_count} files → ~{estimated_chunks} chunks[/blue]")
    
    else:
        console.print("\n[bold red]Setup incomplete. Please fix the issues above.[/bold red]")
        
        fixes = []
        if not api_ok:
            fixes.append("Set OPENAI_API_KEY environment variable")
        if not deps_ok:
            fixes.append("Run: python setup.py")
        if not dirs_ok:
            fixes.append("Create missing directories")
        if not files_ok:
            fixes.append("Run the web scraper first (normalizeWebContent)")
        
        fix_text = "\n".join(f"• {fix}" for fix in fixes)
        console.print(Panel(fix_text, title="🔧 Required Fixes", border_style="red"))

if __name__ == '__main__':
    main()
