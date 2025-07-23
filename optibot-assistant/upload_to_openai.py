#!/usr/bin/env python3
"""
OptiBot Assistant Vector Store Upload Script

This script processes the scraped OptiSigns support articles and uploads them
to OpenAI's Vector Store for use with the OptiBot assistant.

Usage:
    python upload_to_openai.py --input ../normalizeWebContent/output
    python upload_to_openai.py --input ../normalizeWebContent/output --create-assistant
"""

import os
import sys
import click
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.chunking import MarkdownChunker
from utils.openai_client import OpenAIVectorStoreClient
from config import (
    DEFAULT_INPUT_DIR, 
    ASSISTANT_NAME, 
    ASSISTANT_DESCRIPTION, 
    ASSISTANT_INSTRUCTIONS
)

console = Console()


def validate_input_directory(input_dir: Path) -> bool:
    """Validate that input directory exists and contains markdown files."""
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        return False
    
    markdown_files = list(input_dir.glob("*.md"))
    # Exclude INDEX.md
    markdown_files = [f for f in markdown_files if f.name != "INDEX.md"]
    
    if not markdown_files:
        console.print(f"[red]No markdown files found in: {input_dir}[/red]")
        return False
    
    console.print(f"[green]✓ Found {len(markdown_files)} markdown files[/green]")
    return True


def process_markdown_files(input_dir: Path, chunker: MarkdownChunker) -> List[dict]:
    """Process all markdown files into chunks."""
    markdown_files = list(input_dir.glob("*.md"))
    # Exclude INDEX.md as because just a table of contents
    markdown_files = [f for f in markdown_files if f.name != "INDEX.md"]
    
    all_chunks = []
    
    console.print(f"\n[blue]Processing {len(markdown_files)} files...[/blue]")
    
    for file_path in markdown_files:
        console.print(f"Processing: [cyan]{file_path.name}[/cyan]")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            chunks = chunker.chunk_file(str(file_path), content)
            
            console.print(f"  → Created {len(chunks)} chunks")
            all_chunks.extend(chunks)
            
        except Exception as e:
            console.print(f"  [red]Error processing {file_path.name}: {str(e)}[/red]")
    
    return all_chunks


def display_chunking_stats(stats: dict) -> None:
    """Display chunking statistics in a table."""
    table = Table(title="Chunking Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Files Processed", str(stats['total_files']))
    table.add_row("Total Chunks Created", str(stats['total_chunks']))
    table.add_row("Total Characters", f"{stats['total_characters']:,}")
    table.add_row("Average Chunk Size", f"{stats['avg_chunk_size']:.0f} chars")
    
    console.print(table)


def display_upload_stats(stats: dict) -> None:
    """Display upload statistics in a table."""
    table = Table(title="Upload Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Successful Uploads", str(stats['successful_uploads']))
    table.add_row("Failed Uploads", str(stats['failed_uploads']))
    table.add_row("Total Files Uploaded", str(stats['total_files']))
    table.add_row("Vector Store ID", stats['vector_store_id'] or "Not created")
    
    console.print(table)


@click.command()
@click.option(
    '--input', 
    'input_dir',
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_INPUT_DIR,
    help='Input directory containing markdown files'
)
@click.option(
    '--create-assistant',
    is_flag=True,
    help='Create OpenAI Assistant after uploading files'
)
@click.option(
    '--vector-store-name',
    default='OptiSigns Support Articles',
    help='Name for the vector store'
)
def main(input_dir: Path, create_assistant: bool, vector_store_name: str):
    """
    Upload OptiSigns support articles to OpenAI Vector Store.
    
    This script processes markdown files from the web scraper exercise,
    chunks them appropriately, and uploads them to OpenAI for use with
    the OptiBot assistant.
    """
    console.print("[bold blue] OptiBot Vector Store Upload[/bold blue]")
    console.print(f"Input directory: {input_dir}")
    
    if not os.getenv('OPENAI_API_KEY'):
        console.print("[red]OPENAI_API_KEY environment variable not set[/red]")
        console.print("Please set your OpenAI API key:")
        console.print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    if not validate_input_directory(input_dir):
        sys.exit(1)
    
    chunker = MarkdownChunker()
    openai_client = OpenAIVectorStoreClient()
    
    try:
        # Step 1: Process markdown files into chunks
        console.print("\n[bold]Step 1: Processing markdown files[/bold]")
        chunks = process_markdown_files(input_dir, chunker)
        
        if not chunks:
            console.print("[red]No chunks created[/red]")
            sys.exit(1)
        
        chunking_stats = chunker.get_stats()
        display_chunking_stats(chunking_stats)
        
        console.print("\n[bold]Step 2: Creating vector store[/bold]")
        vector_store_id = openai_client.create_vector_store(
            name=vector_store_name,
            description="Support articles for OptiSigns customer support bot"
        )
        
        console.print("\n[bold]Step 3: Uploading chunks to OpenAI[/bold]")
        file_ids = openai_client.upload_chunks_with_progress(chunks)
        
        if not file_ids:
            console.print("[red]No files uploaded successfully[/red]")
            sys.exit(1)
        
        console.print("\n[bold]Step 4: Adding files to vector store[/bold]")
        success = openai_client.add_files_to_vector_store(vector_store_id, file_ids)
        
        if not success:
            console.print("[red]Failed to add files to vector store[/red]")
            sys.exit(1)
        
        assistant_id = None
        if create_assistant:
            console.print("\n[bold]Step 5: Creating OpenAI Assistant[/bold]")
            assistant_id = openai_client.create_assistant(
                name=ASSISTANT_NAME,
                instructions=ASSISTANT_INSTRUCTIONS,
                vector_store_id=vector_store_id
            )
        
        # Display final statistics
        console.print("\n[bold green]Upload Complete![/bold green]")
        upload_stats = openai_client.get_stats()
        display_upload_stats(upload_stats)
        
        openai_client.save_upload_log(chunking_stats)
        
        console.print("\n[bold]Important IDs:[/bold]")
        console.print(f"Vector Store ID: [yellow]{vector_store_id}[/yellow]")
        if assistant_id:
            console.print(f"Assistant ID: [yellow]{assistant_id}[/yellow]")
        
        console.print("\n[bold]Next Steps:[/bold]")
        if not create_assistant:
            console.print("1. Go to OpenAI Playground: https://platform.openai.com/playground/assistants")
            console.print("2. Create a new assistant with the system prompt from README.md")
            console.print(f"3. Attach vector store ID: {vector_store_id}")
        console.print("4. Test with query: 'How do I add a YouTube video?'")
        console.print("5. Take screenshot showing answer with citations")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Upload interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Upload failed: {str(e)}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
