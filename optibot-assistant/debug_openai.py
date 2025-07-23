#!/usr/bin/env python3
"""
Debug OpenAI API connection and vector stores
"""

import os
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

console = Console()

def test_openai_connection():
    """Test OpenAI API connection and vector stores"""
    console.print("[bold blue]OpenAI API Debug Test[/bold blue]")
    console.print()
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        console.print("[red]No OPENAI_API_KEY found in environment[/red]")
        console.print("Please set your API key first:")
        console.print("1. Run: [cyan]python setup_env.py[/cyan]")
        console.print("2. Or set manually: [cyan]$env:OPENAI_API_KEY='your-key'[/cyan]")
        return False
    
    console.print(f"[green]API key found: {api_key[:8]}...{api_key[-4:]}[/green]")
    
    try:
        import openai
        console.print(f"[green]OpenAI library v{openai.__version__}[/green]")
        
        client = openai.OpenAI(api_key=api_key)
        console.print("[green]OpenAI client initialized[/green]")
        
        if hasattr(client, 'beta'):
            console.print("[green]Beta client available[/green]")
            
            if hasattr(client.beta, 'vector_stores'):
                console.print("[green]Vector stores API available[/green]")
                
                try:
                    # Just list existing vector stores
                    vector_stores = client.beta.vector_stores.list(limit=1)
                    console.print(f"[green]Vector stores API working! Found {len(vector_stores.data)} existing stores[/green]")
                    
                    return True
                    
                except Exception as e:
                    console.print(f"[red]Vector stores API call failed: {e}[/red]")
                    
                    if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                        console.print("[yellow]💡 This looks like an API key issue[/yellow]")
                        console.print("Please check:")
                        console.print("1. Your API key is correct")
                        console.print("2. Your OpenAI account has credits")
                        console.print("3. Your API key has the right permissions")
                    
                    return False
                    
            else:
                console.print("[red]client.beta.vector_stores not found[/red]")
                console.print("This is strange - your OpenAI version should support this...")
                return False
                
        else:
            console.print("[red]client.beta not found[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]OpenAI client error: {e}[/red]")
        return False

def test_simple_openai_call():
    """Test a simple OpenAI API call"""
    console.print()
    console.print("[bold]Testing basic OpenAI API call...[/bold]")
    
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        models = client.models.list()
        console.print(f"[green]Basic API working! Found {len(models.data)} models[/green]")
        
        model_names = [model.id for model in models.data[:3]]
        console.print(f"Sample models: {', '.join(model_names)}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Basic API call failed: {e}[/red]")
        return False

def main():
    """Main debug function"""
    success1 = test_openai_connection()
    success2 = test_simple_openai_call()
    
    console.print()
    if success1 and success2:
        console.print("[bold green]Everything looks good! Try running the upload again:[/bold green]")
        console.print("[cyan]python upload_to_openai.py --input ../normalizeWebContent/output --create-assistant[/cyan]")
    else:
        console.print("[bold red]Issues found. Please fix the problems above.[/bold red]")

if __name__ == '__main__':
    main()
