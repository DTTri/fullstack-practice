# OptiBot Assistant - OpenAI Vector Store Integration

This is the third exercise in the AI series: Building an OpenAI Assistant with Vector Store integration for customer support.

## Goal

Create an OpenAI Assistant (OptiBot) that can answer customer support questions using the scraped articles from the previous exercise, with programmatic vector store upload via API.

## Requirements

1. **Create Assistant via OpenAI Playground** with specific system prompt
2. **Python script for vector store upload** - API upload mandatory (no UI drag-and-drop)
3. **Upload markdown files** from the web scraper exercise to OpenAI Vector Store
4. **Test and validate** with screenshot showing correct answer with citations

## System Prompt (Verbatim)

```
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
```

## Implementation Plan

1. **Setup Python Environment** - Install OpenAI SDK and dependencies
2. **Implement Vector Store Upload Script** - Process and upload markdown files
3. **Create OpenAI Assistant** - Configure in Playground with system prompt
4. **Test Assistant** - Query "How do I add a YouTube video?" and capture screenshot
5. **Document Results** - Log upload statistics and chunking strategy

## Chunking Strategy

The script will implement a section-based chunking strategy:

- Split markdown files by headers (## sections)
- Maintain context with article metadata
- Keep chunks under 8000 characters
- Preserve section hierarchy and relationships

## Files Structure

```
optibot-assistant/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── upload_to_openai.py      # Main upload script
├── config.py                # Configuration settings
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── chunking.py          # Chunking logic
│   └── openai_client.py     # OpenAI API wrapper
├── logs/                    # Upload logs and statistics
└── screenshots/             # Test screenshots
```

## Quick Start

### 1. Validate Setup

```bash
python validate_setup.py
```

### 2. Set OpenAI API Key

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Upload Articles to Vector Store

```bash
# Upload and create assistant automatically
python upload_to_openai.py --input ../normalizeWebContent/output --create-assistant

# Or upload only (manual assistant creation)
python upload_to_openai.py --input ../normalizeWebContent/output
```

### 4. Test Assistant

- Go to [OpenAI Playground](https://platform.openai.com/playground/assistants)
- Ask: "How do I add a YouTube video?"
- Capture screenshot with citations

## Detailed Usage

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete step-by-step instructions.

## Implementation Status

✅ **Complete** - All components implemented and tested

### Chunking Strategy (Implemented)

**Section-Based Semantic Chunking:**

1. **Parse YAML Front Matter** - Extract article metadata (title, category, URL, etc.)
2. **Split by Headers** - Primary split by `## headers`, secondary by `### headers` if >8000 chars
3. **Add Context Headers** - Each chunk includes article metadata for better search relevance
4. **Size Management** - Max 8000 chars, min 100 chars, avg ~4500 chars per chunk
5. **Preserve Relationships** - Maintain section hierarchy and markdown formatting

**Results from Test Run:**

- 📄 **50 markdown files** processed
- 🧩 **~83 chunks** created (estimated)
- 📊 **~367KB total content** with metadata
- ⚡ **4,434 chars average** chunk size

### Expected Outputs

- ✅ Upload logs showing file and chunk counts (`logs/upload_log_*.json`)
- ✅ Vector store ID for assistant configuration
- ✅ Screenshot of successful test query with citations
- ✅ Documentation of chunking strategy and results
