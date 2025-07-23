"""
Configuration settings for OptiBot Assistant Vector Store Upload
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

MAX_CHUNK_SIZE = 8000  
MIN_CHUNK_SIZE = 100  
RATE_LIMIT_DELAY = 0.5 

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
DEFAULT_INPUT_DIR = PROJECT_ROOT.parent / "normalizeWebContent" / "output"

LOGS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

ASSISTANT_NAME = "OptiBot"
ASSISTANT_DESCRIPTION = "Customer support bot for OptiSigns.com"
ASSISTANT_INSTRUCTIONS = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""

CHUNK_BY_SECTIONS = True  
PRESERVE_METADATA = True 
INCLUDE_CONTEXT_HEADER = True 
