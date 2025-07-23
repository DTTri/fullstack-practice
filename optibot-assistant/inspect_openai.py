#!/usr/bin/env python3
"""
Inspect OpenAI library to see what's available
"""

import os
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

def inspect_openai():
    """Inspect OpenAI library structure"""
    console.print("[bold blue]OpenAI Library Inspection[/bold blue]")
    console.print()
    
    try:
        import openai
        console.print(f"OpenAI version: {openai.__version__}")
        console.print(f"OpenAI file location: {openai.__file__}")
        console.print()
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        console.print("[bold]Beta client attributes:[/bold]")
        beta_attrs = [attr for attr in dir(client.beta) if not attr.startswith('_')]
        for attr in sorted(beta_attrs):
            console.print(f"  • {attr}")
        
        console.print()
        
        console.print("[bold]Looking for vector store related attributes:[/bold]")
        all_attrs = dir(client.beta)
        vector_attrs = [attr for attr in all_attrs if 'vector' in attr.lower()]
        if vector_attrs:
            console.print("Found vector-related attributes:")
            for attr in vector_attrs:
                console.print(f"  • {attr}")
        else:
            console.print("No vector-related attributes found")
        
        store_attrs = [attr for attr in all_attrs if 'store' in attr.lower()]
        if store_attrs:
            console.print("Found store-related attributes:")
            for attr in store_attrs:
                console.print(f"  • {attr}")
        
        console.print()
        
        console.print("[bold]Testing alternative API paths:[/bold]")
        
        if hasattr(client, 'vector_stores'):
            console.print("Found client.vector_stores")
        else:
            console.print("No client.vector_stores")
        
        if hasattr(client, 'files'):
            console.print("Found client.files")
            files_attrs = [attr for attr in dir(client.files) if not attr.startswith('_')]
            console.print(f"Files attributes: {files_attrs}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error inspecting OpenAI: {e}[/red]")
        return False

def test_alternative_imports():
    """Test different ways to import OpenAI"""
    console.print()
    console.print("[bold blue]🧪 Testing Alternative Import Methods[/bold blue]")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        console.print("Direct import works")
        
        if hasattr(client.beta, 'vector_stores'):
            console.print("vector_stores found with direct import")
            return True
        else:
            console.print("vector_stores still missing with direct import")
    except Exception as e:
        console.print(f"Direct import failed: {e}")
    
    try:
        import openai
        console.print(f"OpenAI module location: {openai.__file__}")
        console.print(f"OpenAI module dir: {dir(openai)}")
        
        import sys
        openai_paths = [path for path in sys.path if 'openai' in path.lower()]
        if openai_paths:
            console.print(f"Potential OpenAI paths in sys.path: {openai_paths}")
        
    except Exception as e:
        console.print(f"Module inspection failed: {e}")
    
    return False

def main():
    """Main inspection function"""
    inspect_openai()
    test_alternative_imports()
    
    console.print()
    console.print("[bold yellow]Possible Solutions:[/bold yellow]")
    console.print("1. Try reinstalling OpenAI: [cyan]python -m pip uninstall openai && python -m pip install openai[/cyan]")
    console.print("2. Check for multiple Python environments")
    console.print("3. Try using the legacy files API instead of vector stores")

if __name__ == '__main__':
    main()
