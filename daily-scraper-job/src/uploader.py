"""
Vector store uploader with batch processing and error handling.
"""

import time
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI not installed. Run: pip install openai")
    OpenAI = None

from config.settings import Settings


class VectorStoreUploader:
    """Uploads articles to OpenAI Vector Store with batch processing."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        if OpenAI is None:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.vector_store_id = None
        self.assistant_id = None
        
        # Upload statistics
        self.stats = {
            'total_articles': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'chunks_created': 0,
            'files_uploaded': 0
        }
    
    def upload_articles(self, articles: List[Dict[str, Any]], operation: str = 'add') -> int:
        """
        Upload articles to the vector store.
        
        Args:
            articles: List of article dictionaries
            operation: 'add' for new articles, 'update' for existing ones
            
        Returns:
            Number of successfully uploaded articles
        """
        if not articles:
            self.logger.info("📤 No articles to upload")
            return 0
        
        self.logger.info(f"📤 Starting {operation} operation for {len(articles)} articles")
        self.stats['total_articles'] = len(articles)
        
        try:
            # Ensure vector store exists
            if not self._ensure_vector_store():
                self.logger.error("❌ Failed to create or find vector store")
                return 0
            
            # Process articles in batches
            successful_count = 0
            batch_size = self.settings.batch_size
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(articles) + batch_size - 1) // batch_size
                
                self.logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} articles)")
                
                batch_success = self._upload_batch(batch, operation)
                successful_count += batch_success
                
                # Rate limiting between batches
                if i + batch_size < len(articles):
                    time.sleep(self.settings.api_rate_limit)
            
            self.logger.info(f"✅ Upload completed: {successful_count}/{len(articles)} successful")
            self._log_upload_stats()
            
            return successful_count
            
        except Exception as e:
            self.logger.error(f"❌ Upload failed: {e}")
            return 0
    
    def _upload_batch(self, articles: List[Dict[str, Any]], operation: str) -> int:
        """Upload a batch of articles."""
        successful_count = 0
        
        for article in articles:
            try:
                if self._upload_single_article(article, operation):
                    successful_count += 1
                    self.stats['successful_uploads'] += 1
                else:
                    self.stats['failed_uploads'] += 1
                
                # Rate limiting between individual uploads
                time.sleep(self.settings.api_rate_limit)
                
            except Exception as e:
                self.logger.error(f"❌ Failed to upload article {article.get('id', 'unknown')}: {e}")
                self.stats['failed_uploads'] += 1
        
        return successful_count
    
    def _upload_single_article(self, article: Dict[str, Any], operation: str) -> bool:
        """Upload a single article to the vector store."""
        article_id = article.get('id', 'unknown')
        title = article.get('title', 'Untitled')
        
        try:
            # If updating, try to remove existing files first
            if operation == 'update':
                self._remove_existing_files(article_id)
            
            # Create chunks from article content
            chunks = self._create_chunks(article)
            self.stats['chunks_created'] += len(chunks)
            
            if not chunks:
                self.logger.warning(f"⚠️ No chunks created for article {article_id}")
                return False
            
            # Upload chunks as files
            file_ids = []
            for i, chunk in enumerate(chunks):
                file_id = self._upload_chunk_as_file(chunk, article_id, i)
                if file_id:
                    file_ids.append(file_id)
                    self.stats['files_uploaded'] += 1
            
            if not file_ids:
                self.logger.error(f"❌ No files uploaded for article {article_id}")
                return False
            
            # Add files to vector store
            if self._add_files_to_vector_store(file_ids):
                self.logger.debug(f"✅ Uploaded article {article_id}: {title[:50]}...")
                return True
            else:
                self.logger.error(f"❌ Failed to add files to vector store for article {article_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error uploading article {article_id}: {e}")
            return False
    
    def _create_chunks(self, article: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create chunks from article content."""
        content = article.get('content', '')
        title = article.get('title', 'Untitled')
        url = article.get('url', '')
        
        if len(content) <= self.settings.chunk_size:
            # Single chunk
            return [{
                'content': self._format_chunk_content(article, content),
                'metadata': {
                    'article_id': article.get('id'),
                    'title': title,
                    'url': url,
                    'chunk_index': 0,
                    'total_chunks': 1
                }
            }]
        
        # Multiple chunks
        chunks = []
        chunk_size = self.settings.chunk_size
        overlap = 200  # Character overlap between chunks
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence ending within last 200 characters
                sentence_end = content.rfind('.', end - 200, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk_content = content[start:end].strip()
            
            if len(chunk_content) >= self.settings.min_chunk_size:
                chunks.append({
                    'content': self._format_chunk_content(article, chunk_content, chunk_index),
                    'metadata': {
                        'article_id': article.get('id'),
                        'title': title,
                        'url': url,
                        'chunk_index': chunk_index,
                        'total_chunks': 0  # Will be updated after all chunks are created
                    }
                })
                chunk_index += 1
            
            start = max(end - overlap, start + 1)  # Ensure progress
        
        # Update total_chunks in metadata
        for chunk in chunks:
            chunk['metadata']['total_chunks'] = len(chunks)
        
        return chunks
    
    def _format_chunk_content(self, article: Dict[str, Any], content: str, chunk_index: int = 0) -> str:
        """Format chunk content with metadata header."""
        title = article.get('title', 'Untitled')
        url = article.get('url', '')
        category = article.get('category', 'Unknown')
        section = article.get('section', 'Unknown')
        
        header = f"""# {title}

**Category:** {category}
**Section:** {section}
**URL:** {url}
**Article ID:** {article.get('id', 'unknown')}
"""
        
        if chunk_index > 0:
            header += f"**Chunk:** {chunk_index + 1}\n"
        
        header += "\n---\n\n"
        
        return header + content
    
    def _upload_chunk_as_file(self, chunk: Dict[str, str], article_id: str, chunk_index: int) -> Optional[str]:
        """Upload a chunk as a file to OpenAI."""
        try:
            # Create filename
            filename = f"{article_id}_chunk_{chunk_index}.md"
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(chunk['content'])
                temp_path = temp_file.name
            
            try:
                # Upload to OpenAI
                with open(temp_path, 'rb') as f:
                    file_response = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                
                return file_response.id
                
            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to upload chunk {chunk_index} for article {article_id}: {e}")
            return None
    
    def _add_files_to_vector_store(self, file_ids: List[str]) -> bool:
        """Add uploaded files to the vector store."""
        try:
            self.client.beta.vector_stores.file_batches.create(
                vector_store_id=self.vector_store_id,
                file_ids=file_ids
            )
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add files to vector store: {e}")
            return False
    
    def _ensure_vector_store(self) -> bool:
        """Ensure vector store exists, create if necessary."""
        if self.vector_store_id:
            return True
        
        try:
            # Try to find existing vector store
            vector_stores = self.client.beta.vector_stores.list()
            
            for vs in vector_stores.data:
                if vs.name == self.settings.vector_store_name:
                    self.vector_store_id = vs.id
                    self.logger.info(f"📚 Found existing vector store: {vs.id}")
                    return True
            
            # Create new vector store
            vector_store = self.client.beta.vector_stores.create(
                name=self.settings.vector_store_name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 365
                }
            )
            
            self.vector_store_id = vector_store.id
            self.logger.info(f"📚 Created new vector store: {vector_store.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to ensure vector store: {e}")
            return False
    
    def _remove_existing_files(self, article_id: str):
        """Remove existing files for an article (for updates)."""
        try:
            # List files in vector store
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=self.vector_store_id
            )
            
            # Find files for this article
            files_to_remove = []
            for file in files.data:
                # Check if file belongs to this article (by filename pattern)
                if file.id.startswith(f"{article_id}_"):
                    files_to_remove.append(file.id)
            
            # Remove files
            for file_id in files_to_remove:
                self.client.beta.vector_stores.files.delete(
                    vector_store_id=self.vector_store_id,
                    file_id=file_id
                )
            
            if files_to_remove:
                self.logger.debug(f"🗑️ Removed {len(files_to_remove)} existing files for article {article_id}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to remove existing files for article {article_id}: {e}")
    
    def _log_upload_stats(self):
        """Log upload statistics."""
        self.logger.info("📊 Upload Statistics:")
        self.logger.info(f"  Total articles: {self.stats['total_articles']}")
        self.logger.info(f"  Successful uploads: {self.stats['successful_uploads']}")
        self.logger.info(f"  Failed uploads: {self.stats['failed_uploads']}")
        self.logger.info(f"  Chunks created: {self.stats['chunks_created']}")
        self.logger.info(f"  Files uploaded: {self.stats['files_uploaded']}")
        
        if self.stats['total_articles'] > 0:
            success_rate = (self.stats['successful_uploads'] / self.stats['total_articles']) * 100
            self.logger.info(f"  Success rate: {success_rate:.1f}%")
    
    def get_stats(self) -> Dict[str, int]:
        """Get upload statistics."""
        return self.stats.copy()
    
    def get_vector_store_id(self) -> Optional[str]:
        """Get the vector store ID."""
        return self.vector_store_id
