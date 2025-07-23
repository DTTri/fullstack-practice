#!/usr/bin/env python3
"""
Fallback upload script using legacy OpenAI Files API
(for when vector_stores API is not available)
"""

import os
import sys
import click
import time
from pathlib import Path
from typing import List
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))

from utils.chunking import MarkdownChunker
from config import DEFAULT_INPUT_DIR, RATE_LIMIT_DELAY

console = Console()

class LegacyOpenAIClient:
    """OpenAI client using legacy Files API"""
    
    def __init__(self):
        import openai
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.stats = {
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_files': 0,
            'file_ids': []
        }
    
    def upload_file(self, content: str, filename: str) -> str:
        """Upload a single file to OpenAI"""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Upload to OpenAI
                with open(temp_path, 'rb') as f:
                    file_response = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                
                self.stats['successful_uploads'] += 1
                self.stats['file_ids'].append(file_response.id)
                
                return file_response.id
                
            finally:
                # Clean up temp file
                os.unlink(temp_path)
            
        except Exception as e:
            console.print(f"[red]✗ Failed to upload {filename}: {str(e)}[/red]")
            self.stats['failed_uploads'] += 1
            return None
    
    def upload_chunks_with_progress(self, chunks: List[dict]) -> List[str]:
        """Upload chunks with progress tracking"""
        file_ids = []
        
        with Progress() as progress:
            task = progress.add_task("[blue]Uploading chunks...", total=len(chunks))
            
            for chunk in chunks:
                file_id = self.upload_file(chunk['content'], chunk['filename'])
                
                if file_id:
                    file_ids.append(file_id)
                    progress.console.print(f"[green]✓ {chunk['filename']}: {file_id}[/green]")
                else:
                    progress.console.print(f"[red]✗ Failed: {chunk['filename']}[/red]")
                
                progress.update(task, advance=1)
                time.sleep(RATE_LIMIT_DELAY)
        
        self.stats['total_files'] = len(chunks)
        return file_ids
    
    def create_assistant(self, name: str, instructions: str, file_ids: List[str]) -> str:
        """Create assistant with uploaded files"""
        try:
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_stores": [{
                            "file_ids": file_ids
                        }]
                    }
                }
            )
            
            console.print(f"[green]Assistant created: {assistant.id}[/green]")
            return assistant.id
            
        except Exception as e:
            console.print(f"[red]Failed to create assistant: {str(e)}[/red]")
            return None
    
    def get_stats(self) -> dict:
        """Get upload statistics"""
        return self.stats.copy()

def validate_input_directory(input_dir: Path) -> bool:
    """Validate that input directory exists and contains markdown files"""
    if not input_dir.exists():
        console.print(f"[red]✗ Input directory not found: {input_dir}[/red]")
        return False
    
    markdown_files = list(input_dir.glob("*.md"))
    markdown_files = [f for f in markdown_files if f.name != "INDEX.md"]
    
    if not markdown_files:
        console.print(f"[red]No markdown files found in: {input_dir}[/red]")
        return False
    
    console.print(f"[green]Found {len(markdown_files)} markdown files[/green]")
    return True

def process_markdown_files(input_dir: Path, chunker: MarkdownChunker) -> List[dict]:
    """Process all markdown files into chunks"""
    markdown_files = list(input_dir.glob("*.md"))
    markdown_files = [f for f in markdown_files if f.name != "INDEX.md"]
    
    all_chunks = []
    
    console.print(f"\n[blue]Processing {len(markdown_files)} files...[/blue]")
    
    for file_path in markdown_files:
        console.print(f"Processing: [cyan]{file_path.name}[/cyan]")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            chunks = chunker.chunk_file(str(file_path), content)
            
            console.print(f"  Created {len(chunks)} chunks")
            all_chunks.extend(chunks)
            
        except Exception as e:
            console.print(f"  [red]Error processing {file_path.name}: {str(e)}[/red]")
    
    return all_chunks

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
def main(input_dir: Path, create_assistant: bool):
    """
    Fallback upload script using legacy OpenAI Files API
    """
    console.print("[bold blue]OptiBot Fallback Upload (Legacy Files API)[/bold blue]")
    console.print(f"Input directory: {input_dir}")
    
    if not os.getenv('OPENAI_API_KEY'):
        console.print("[red]OPENAI_API_KEY environment variable not set[/red]")
        sys.exit(1)
    
    if not validate_input_directory(input_dir):
        sys.exit(1)
    
    chunker = MarkdownChunker()
    openai_client = LegacyOpenAIClient()
    
    try:
        # Step 1: Process markdown files into chunks
        console.print("\n[bold]Step 1: Processing markdown files[/bold]")
        chunks = process_markdown_files(input_dir, chunker)
        
        if not chunks:
            console.print("[red]No chunks created[/red]")
            sys.exit(1)
        
        stats = chunker.get_stats()
        console.print(f"\n[green]Created {stats['total_chunks']} chunks from {stats['total_files']} files[/green]")
        
        # Step 2: Upload chunks to OpenAI
        console.print("\n[bold]Step 2: Uploading chunks to OpenAI Files API[/bold]")
        file_ids = openai_client.upload_chunks_with_progress(chunks)
        
        if not file_ids:
            console.print("[red]No files uploaded successfully[/red]")
            sys.exit(1)
        
        console.print(f"\n[green]Uploaded {len(file_ids)} files successfully[/green]")
        
        assistant_id = None
        if create_assistant:
            console.print("\n[bold]Step 3: Creating OpenAI Assistant[/bold]")
            
            instructions = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""
            
            assistant_id = openai_client.create_assistant(
                name="OptiBot",
                instructions=instructions,
                file_ids=file_ids
            )
        
        console.print("\n[bold green] Upload Complete![/bold green]")
        console.print(f"Files uploaded: {len(file_ids)}")
        console.print(f"Sample file IDs: {file_ids[:3]}...")
        
        if assistant_id:
            console.print(f"Assistant ID: [yellow]{assistant_id}[/yellow]")
        
        console.print("\n[bold]Next Steps:[/bold]")
        if not create_assistant:
            console.print("1. Go to OpenAI Playground: https://platform.openai.com/playground/assistants")
            console.print("2. Create a new assistant and attach the uploaded files")
        console.print("3. Test with query: 'How do I add a YouTube video?'")        
    except Exception as e:
        console.print(f"\n[red]✗ Upload failed: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
