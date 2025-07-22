# OptiSigns Support Article Scraper

A TypeScript tool to scrape and normalize articles from support.optisigns.com, converting them to clean Markdown format while preserving links, code blocks, and headings.

## Features

- **Zendesk API Integration**: Uses the official Zendesk Help Center API for reliable data access
- **Clean Markdown Conversion**: Converts HTML to well-formatted Markdown with proper structure

## Installation

1. Clone or download this project
2. Install dependencies:

```bash
npm install
```

3. Build the project:

```bash
npm run build
```

## Usage

### Basic Scraping

Scrape articles with default settings (50 articles max):

```bash
npm run dev scrape
```

### Advanced Options

```bash
npm run dev scrape \
  --output ./my-articles \
  --max-articles 100 \
  --delay 2000 \
  --retries 5 \
  --log-file scraping.log
```

### Available Commands

#### `scrape` - Main scraping command

```bash
npm run dev scrape [options]
```

**Options:**

- `-o, --output <dir>` - Output directory for markdown files (default: `./output`)
- `-m, --max-articles <number>` - Maximum number of articles to scrape (default: `50`)
- `-d, --delay <ms>` - Delay between requests in milliseconds (default: `1000`)
- `-r, --retries <number>` - Number of retries for failed requests (default: `3`)
- `-l, --log-file <file>` - Log file path (optional)
- `--no-index` - Skip generating index file

#### `validate` - Validate scraped files

```bash
npm run dev validate --input ./output
```

Checks that all markdown files have proper structure and required metadata.

#### `stats` - Show statistics

```bash
npm run dev stats --input ./output
```

Displays statistics about scraped articles including file counts, sizes, and category distribution.

## Output Structure

The scraper creates the following structure:

```
output/
├── INDEX.md                    # Generated index of all articles
├── optisigns-getting-started-guide.md
├── windows.md
├── amazon-firestick.md
└── ...
```

### Article Format

Each article is saved as a Markdown file with YAML front matter:

```markdown
---
title: "OptiSigns - Getting Started Guide"
id: 18823504383891
url: https://support.optisigns.com/hc/en-us/articles/18823504383891
category: "Welcome to OptiSigns"
section: "Getting Started"
created_at: 2023-08-15T10:30:00Z
updated_at: 2023-12-01T14:22:00Z
vote_sum: 15
vote_count: 20
---

# OptiSigns - Getting Started Guide

Welcome to OptiSigns! This guide will help you...

## Setting Up Your Account

1. Sign up at [app.optisigns.com](https://app.optisigns.com)
2. Verify your email address
3. Complete your profile

...
```

## Technical Details

### Architecture

- **ZendeskClient**: Handles API communication with Zendesk Help Center
- **MarkdownConverter**: Converts HTML to clean Markdown using Turndown.js
- **ArticleScraper**: Main orchestrator that processes articles
- **Utils**: Logging, retry logic, progress tracking, and file operations

### Rate Limiting

The scraper implements rate limiting:

- Default 1-second delay between requests
- Exponential backoff for retries
- Configurable delays and retry counts

## Development

### Scripts

- `npm run build` - Compile TypeScript to JavaScript
- `npm run dev` - Run with ts-node for development
- `npm start` - Run compiled JavaScript
- `npm run clean` - Remove build artifacts

### Project Structure

```
src/
├── index.ts              # CLI interface and main entry point
├── types.ts              # TypeScript type definitions
├── zendesk-client.ts     # Zendesk API client
├── markdown-converter.ts # HTML to Markdown conversion
├── article-scraper.ts    # Main scraping logic
└── utils.ts              # Utilities (logging, retry, etc.)
```

## Requirements

- Node.js 16+
- TypeScript 5+
- Internet connection for API access

## Limitations

- Requires public access to the Zendesk Help Center API
- Rate limited to prevent overwhelming the server
- Some complex HTML structures may not convert perfectly to Markdown

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
