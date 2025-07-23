#!/usr/bin/env python3
"""
Check OpenAI library version and compatibility
"""

from rich.console import Console
from rich.table import Table

console = Console()

def check_openai_version():
    """Check OpenAI library version and features"""
    console.print("[bold blue]OpenAI Library Version Check[/bold blue]")
    console.print()
    
    try:
        import openai
        version = openai.__version__
        
        console.print(f"[green]OpenAI library installed: v{version}[/green]")
        
        from packaging import version as pkg_version
        
        if pkg_version.parse(version) >= pkg_version.parse("1.3.0"):
            console.print("[green]Version supports vector stores[/green]")
            
            try:
                client = openai.OpenAI(api_key="test")
                hasattr(client.beta, 'vector_stores')
                console.print("[green]Vector stores API available[/green]")
                
            except Exception as e:
                console.print(f"[yellow]API test failed (expected with test key): {e}[/yellow]")
                
        else:
            console.print(f"[red]Version {version} is too old for vector stores[/red]")
            console.print("[yellow]Please upgrade: pip install --upgrade openai>=1.3.0[/yellow]")
            return False
            
    except ImportError:
        console.print("[red]OpenAI library not installed[/red]")
        console.print("[yellow]Please install: pip install openai>=1.3.0[/yellow]")
        return False
    
    except Exception as e:
        console.print(f"[red]Error checking OpenAI library: {e}[/red]")
        return False
    
    console.print()
    console.print("[bold]Checking other dependencies:[/bold]")
    
    deps = [
        ("python-dotenv", "dotenv"),
        ("pyyaml", "yaml"),
        ("click", "click"),
        ("rich", "rich"),
        ("packaging", "packaging")
    ]
    
    table = Table()
    table.add_column("Package", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version", style="yellow")
    
    for package_name, import_name in deps:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'Unknown')
            table.add_row(package_name, "Installed", version)
        except ImportError:
            table.add_row(package_name, "Missing", "Not installed")
    
    console.print(table)
    
    return True

def main():
    """Main check function"""
    success = check_openai_version()
    
    if success:
        console.print()
        console.print("[bold green]Ready to run OptiBot upload![/bold green]")
        console.print("[cyan]python upload_to_openai.py --input ../normalizeWebContent/output --create-assistant[/cyan]")
    else:
        console.print()
        console.print("[bold red]Please fix the issues above before running OptiBot[/bold red]")

if __name__ == '__main__':
    main()
