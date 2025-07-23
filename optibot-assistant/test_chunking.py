#!/usr/bin/env python3
"""
Test script to demonstrate chunking strategy without uploading to OpenAI.
This shows how the markdown files would be processed and chunked.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent))

from utils.chunking import MarkdownChunker

console = Console()

def test_chunking_strategy():
    """Test the chunking strategy on a sample of markdown files."""
    
    input_dir = Path("../normalizeWebContent/output")
    
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        return
    
    markdown_files = [f for f in input_dir.glob("*.md") if f.name != "INDEX.md"]
    
    if not markdown_files:
        console.print("[red]No markdown files found[/red]")
        return
    
    console.print(f"[blue]📄 Found {len(markdown_files)} markdown files[/blue]")
    
    chunker = MarkdownChunker()
    
    sample_files = markdown_files[:3]
    all_chunks = []
    
    console.print("\n[bold]🔍 Processing sample files to demonstrate chunking:[/bold]")
    
    for file_path in sample_files:
        console.print(f"\n[cyan]Processing: {file_path.name}[/cyan]")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            chunks = chunker.chunk_file(str(file_path), content)
            all_chunks.extend(chunks)
            
            table = Table(title=f"Chunks for {file_path.name}")
            table.add_column("Chunk", style="cyan")
            table.add_column("Section", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Level", style="blue")
            
            for i, chunk in enumerate(chunks, 1):
                table.add_row(
                    f"Chunk {i}",
                    chunk['section_title'][:50] + "..." if len(chunk['section_title']) > 50 else chunk['section_title'],
                    f"{chunk['character_count']} chars",
                    f"Level {chunk['section_level']}"
                )
            
            console.print(table)
            
            if chunks:
                sample_chunk = chunks[0]
                sample_content = sample_chunk['content'][:500] + "..." if len(sample_chunk['content']) > 500 else sample_chunk['content']
                
                console.print(Panel(
                    sample_content,
                    title=f"Sample Content - {sample_chunk['filename']}",
                    border_style="green"
                ))
            
        except Exception as e:
            console.print(f"[red]Error processing {file_path.name}: {str(e)}[/red]")
    
    # Show overall statistics
    stats = chunker.get_stats()
    
    console.print("\n[bold]📊 Chunking Statistics (Sample):[/bold]")
    stats_table = Table()
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Files Processed", str(stats['total_files']))
    stats_table.add_row("Total Chunks", str(stats['total_chunks']))
    stats_table.add_row("Total Characters", f"{stats['total_characters']:,}")
    stats_table.add_row("Average Chunk Size", f"{stats['avg_chunk_size']:.0f} chars")
    
    console.print(stats_table)
    
    # Estimate for all files
    avg_chunks_per_file = stats['total_chunks'] / stats['total_files'] if stats['total_files'] > 0 else 0
    estimated_total_chunks = int(avg_chunks_per_file * len(markdown_files))
    
    console.print(f"\n[bold]📈 Estimated totals for all {len(markdown_files)} files:[/bold]")
    console.print(f"Estimated total chunks: [yellow]{estimated_total_chunks}[/yellow]")
    console.print(f"Estimated total size: [yellow]{stats['avg_chunk_size'] * estimated_total_chunks / 1024:.1f} KB[/yellow]")

def show_chunking_strategy():
    """Display the chunking strategy explanation."""
    
    strategy_text = """
[bold]Chunking Strategy Explanation:[/bold]

1. [cyan]Parse YAML Front Matter[/cyan]
   • Extract article metadata (title, category, URL, etc.)
   • Remove front matter from content processing

2. [cyan]Split by Headers[/cyan]
   • Primary split: ## headers (main sections)
   • Secondary split: ### headers (if section > 8000 chars)
   • Preserve section hierarchy and context

3. [cyan]Add Context Headers[/cyan]
   • Each chunk includes article metadata
   • Article title, category, section, URL
   • Content section name and update date

4. [cyan]Size Management[/cyan]
   • Maximum chunk size: 8000 characters
   • Minimum chunk size: 100 characters
   • Average chunk size: ~2000-4000 characters

5. [cyan]Preserve Relationships[/cyan]
   • Maintain parent-child section relationships
   • Include full section path in chunk titles
   • Keep markdown formatting intact

[bold]Benefits:[/bold]
• Semantic chunking preserves meaning
• Context headers improve search relevance
• Proper size limits ensure embedding quality
• Metadata enables accurate citations
    """
    
    console.print(Panel(strategy_text, title="Chunking Strategy", border_style="blue"))

if __name__ == '__main__':
    console.print("[bold blue]OptiBot Chunking Strategy Test[/bold blue]")
    
    show_chunking_strategy()
    test_chunking_strategy()
    
    console.print("\n[bold green]Chunking test complete![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Set OPENAI_API_KEY environment variable")
    console.print("2. Run: python upload_to_openai.py --input ../normalizeWebContent/output")
    console.print("3. Create assistant in OpenAI Playground")
    console.print("4. Test with 'How do I add a YouTube video?' query")
