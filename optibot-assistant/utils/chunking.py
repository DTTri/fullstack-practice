"""
Chunking utilities for processing markdown files for OpenAI Vector Store.

Chunking Strategy:
1. Parse YAML front matter to extract article metadata
2. Split content by ## headers (main sections)
3. Further split by ### headers if sections are too large
4. Preserve context with metadata headers
5. Maintain section hierarchy and relationships
"""

import re
import yaml
from typing import List, Dict, Any, Tuple
from config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE


class MarkdownChunker:
    """Handles chunking of markdown files for vector store upload."""
    
    def __init__(self):
        self.stats = {
            'total_files': 0,
            'total_chunks': 0,
            'total_characters': 0,
            'avg_chunk_size': 0
        }
    
    def parse_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract YAML front matter from markdown content.
        
        Returns:
            Tuple of (metadata_dict, content_without_frontmatter)
        """
        metadata = {}
        
        front_matter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        
        if front_matter_match:
            try:
                front_matter_text = front_matter_match.group(1)
                metadata = yaml.safe_load(front_matter_text) or {}
                
                content_without_frontmatter = content[front_matter_match.end():]
                
            except yaml.YAMLError as e:
                print(f"Warning: Failed to parse YAML front matter: {e}")
                metadata = self._parse_front_matter_manual(front_matter_match.group(1))
                content_without_frontmatter = content[front_matter_match.end():]
        else:
            content_without_frontmatter = content
        
        return metadata, content_without_frontmatter
    
    def _parse_front_matter_manual(self, front_matter_text: str) -> Dict[str, Any]:
        """Fallback manual parsing for front matter."""
        metadata = {}
        for line in front_matter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                metadata[key] = value
        return metadata
    
    def split_by_headers(self, content: str) -> List[Dict[str, str]]:
        """
        Split content by headers, maintaining hierarchy.
        
        Returns:
            List of sections with title and content
        """
        sections = []
        
        # Split by ## headers (main sections)
        main_sections = re.split(r'\n## ', content)
        
        # Handle content before first ## header
        if main_sections[0].strip():
            intro_content = main_sections[0].strip()
            if len(intro_content) >= MIN_CHUNK_SIZE:
                sections.append({
                    'title': 'Introduction',
                    'content': intro_content,
                    'level': 1
                })
        
        # Process main sections
        for i, section in enumerate(main_sections[1:], 1):
            if not section.strip():
                continue
            
            lines = section.split('\n')
            section_title = lines[0].strip() if lines else f"Section {i}"
            section_content = '\n'.join(lines[1:]).strip()
            
            # If section is too large, split by ### headers
            if len(section_content) > MAX_CHUNK_SIZE:
                subsections = self._split_large_section(section_title, section_content)
                sections.extend(subsections)
            else:
                sections.append({
                    'title': section_title,
                    'content': f"## {section_title}\n\n{section_content}",
                    'level': 2
                })
        
        return sections
    
    def _split_large_section(self, main_title: str, content: str) -> List[Dict[str, str]]:
        """Split large sections by ### headers."""
        subsections = []
        
        # Split by ### headers
        parts = re.split(r'\n### ', content)
        
        # First part (before first ###)
        if parts[0].strip():
            first_part = parts[0].strip()
            if len(first_part) >= MIN_CHUNK_SIZE:
                subsections.append({
                    'title': main_title,
                    'content': f"## {main_title}\n\n{first_part}",
                    'level': 2
                })
        
        # Process subsections
        for j, subsection in enumerate(parts[1:], 1):
            if not subsection.strip():
                continue
            
            lines = subsection.split('\n')
            subsection_title = lines[0].strip() if lines else f"Subsection {j}"
            subsection_content = '\n'.join(lines[1:]).strip()
            
            if len(subsection_content) >= MIN_CHUNK_SIZE:
                full_title = f"{main_title} - {subsection_title}"
                full_content = f"## {main_title}\n\n### {subsection_title}\n\n{subsection_content}"
                
                subsections.append({
                    'title': full_title,
                    'content': full_content,
                    'level': 3
                })
        
        return subsections
    
    def create_chunk_with_context(self, section: Dict[str, str], metadata: Dict[str, Any]) -> str:
        """
        Create final chunk content with metadata context.
        
        Args:
            section: Section dictionary with title and content
            metadata: Article metadata from front matter
            
        Returns:
            Final chunk content with context header
        """
        # Create context header
        context_lines = [
            f"Article: {metadata.get('title', 'Unknown Title')}",
            f"Category: {metadata.get('category', 'Unknown')}",
            f"Section: {metadata.get('section', 'Unknown')}",
            f"Article URL: {metadata.get('url', 'Unknown')}",
            f"Content Section: {section['title']}",
            f"Last Updated: {metadata.get('updated_at', 'Unknown')}",
            "",
            "---",
            ""
        ]
        
        context_header = '\n'.join(context_lines)
        return context_header + section['content']
    
    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Process a single markdown file into chunks.
        
        Args:
            file_path: Path to the file being processed
            content: File content
            
        Returns:
            List of chunk dictionaries
        """
        metadata, clean_content = self.parse_front_matter(content)
        
        sections = self.split_by_headers(clean_content)
        
        chunks = []
        for i, section in enumerate(sections):
            chunk_content = self.create_chunk_with_context(section, metadata)
            
            chunks.append({
                'filename': f"{Path(file_path).stem}_chunk_{i+1}.md",
                'content': chunk_content,
                'section_title': section['title'],
                'section_level': section['level'],
                'character_count': len(chunk_content),
                'metadata': metadata
            })
        
        self.stats['total_files'] += 1
        self.stats['total_chunks'] += len(chunks)
        self.stats['total_characters'] += sum(chunk['character_count'] for chunk in chunks)
        
        return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chunking statistics."""
        stats = self.stats.copy()
        if stats['total_chunks'] > 0:
            stats['avg_chunk_size'] = stats['total_characters'] / stats['total_chunks']
        return stats


from pathlib import Path
