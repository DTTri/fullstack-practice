"""
OpenAI API client wrapper for vector store operations.
"""

import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, TaskID
from config import OPENAI_API_KEY, RATE_LIMIT_DELAY, LOGS_DIR

console = Console()


class OpenAIVectorStoreClient:
    """Handles OpenAI API operations for vector store management."""
    
    def __init__(self, api_key: str = None):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=api_key or OPENAI_API_KEY)
        self.upload_stats = {
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_files': 0,
            'vector_store_id': None,
            'file_ids': []
        }
    
    def create_vector_store(self, name: str, description: str = None) -> str:
        """
        Create a new vector store.
        
        Args:
            name: Name for the vector store
            description: Optional description
            
        Returns:
            Vector store ID
        """
        try:
            console.print(f"[blue]Creating vector store: {name}[/blue]")
            
            vector_store = self.client.beta.vector_stores.create(
                name=name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 365
                }
            )
            
            self.upload_stats['vector_store_id'] = vector_store.id
            console.print(f"[green]✓ Vector store created: {vector_store.id}[/green]")
            
            return vector_store.id
            
        except Exception as e:
            console.print(f"[red]✗ Failed to create vector store: {str(e)}[/red]")
            raise
    
    def upload_file(self, content: str, filename: str) -> Optional[str]:
        """
        Upload a single file to OpenAI.
        
        Args:
            content: File content
            filename: Name for the file
            
        Returns:
            File ID if successful, None if failed
        """
        try:
            temp_path = Path(f"/tmp/{filename}")
            temp_path.write_text(content, encoding='utf-8')
            
            with open(temp_path, 'rb') as f:
                file_response = self.client.files.create(
                    file=f,
                    purpose='assistants'
                )
            
            temp_path.unlink(missing_ok=True)
            
            self.upload_stats['successful_uploads'] += 1
            self.upload_stats['file_ids'].append(file_response.id)
            
            return file_response.id
            
        except Exception as e:
            console.print(f"[red]✗ Failed to upload {filename}: {str(e)}[/red]")
            self.upload_stats['failed_uploads'] += 1
            return None
    
    def add_files_to_vector_store(self, vector_store_id: str, file_ids: List[str]) -> bool:
        """
        Add uploaded files to a vector store.
        
        Args:
            vector_store_id: ID of the vector store
            file_ids: List of file IDs to add
            
        Returns:
            True if successful
        """
        try:
            console.print(f"[blue]Adding {len(file_ids)} files to vector store...[/blue]")
            
            batch_size = 10
            for i in range(0, len(file_ids), batch_size):
                batch = file_ids[i:i + batch_size]
                
                for file_id in batch:
                    self.client.beta.vector_stores.files.create(
                        vector_store_id=vector_store_id,
                        file_id=file_id
                    )
                    time.sleep(RATE_LIMIT_DELAY)
                
                console.print(f"[green]✓ Added batch {i//batch_size + 1} ({len(batch)} files)[/green]")
            
            console.print(f"[green]✓ All files added to vector store[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Failed to add files to vector store: {str(e)}[/red]")
            return False
    
    def upload_chunks_with_progress(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Upload chunks with progress tracking.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of successful file IDs
        """
        file_ids = []
        
        with Progress() as progress:
            task = progress.add_task("[blue]Uploading chunks...", total=len(chunks))
            
            for chunk in chunks:
                file_id = self.upload_file(chunk['content'], chunk['filename'])
                
                if file_id:
                    file_ids.append(file_id)
                    progress.console.print(f"[green]{chunk['filename']}: {file_id}[/green]")
                else:
                    progress.console.print(f"[red]Failed: {chunk['filename']}[/red]")
                
                progress.update(task, advance=1)
                time.sleep(RATE_LIMIT_DELAY)
        
        return file_ids
    
    def create_assistant(self, name: str, instructions: str, vector_store_id: str) -> str:
        """
        Create an OpenAI Assistant with vector store.
        
        Args:
            name: Assistant name
            instructions: System instructions
            vector_store_id: Vector store ID to attach
            
        Returns:
            Assistant ID
        """
        try:
            console.print(f"[blue]Creating assistant: {name}[/blue]")
            
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )
            
            console.print(f"[green]Assistant created: {assistant.id}[/green]")
            return assistant.id
            
        except Exception as e:
            console.print(f"[red]Failed to create assistant: {str(e)}[/red]")
            raise
    
    def save_upload_log(self, chunking_stats: Dict[str, Any]) -> None:
        """Save upload statistics to log file."""
        log_data = {
            'upload_stats': self.upload_stats,
            'chunking_stats': chunking_stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        log_file = LOGS_DIR / f"upload_log_{int(time.time())}.json"
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        console.print(f"[blue]Upload log saved: {log_file}[/blue]")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get upload statistics."""
        return self.upload_stats.copy()
