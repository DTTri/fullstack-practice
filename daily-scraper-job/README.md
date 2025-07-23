# Daily Scraper Job - DigitalOcean Deployment

This is the fourth and final exercise: Deploy the scraper as a daily job on DigitalOcean Platform with delta detection and automated vector store updates.

## Goal

Create a containerized daily job that:

1. **Re-scrapes** OptiSigns support articles
2. **Detects changes** using hash and Last-Modified headers
3. **Uploads only deltas** to OpenAI Vector Store
4. **Logs counts** of added, updated, and skipped articles
5. **Runs daily** on DigitalOcean Platform

## Features

- 🔄 **Delta Detection** - Hash-based and Last-Modified comparison
- 📦 **Dockerized** - Ready for DigitalOcean deployment
- 📊 **Comprehensive Logging** - Added/updated/skipped counts
- ⏰ **Daily Scheduling** - Automated execution
- 🔗 **Job Artifacts** - Accessible logs and run history

## Architecture

```
daily-scraper-job/
├── main.py                 # Main orchestrator script
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
├── config/
│   ├── __init__.py
│   ├── settings.py        # Configuration management
│   └── logging.py         # Logging setup
├── src/
│   ├── __init__.py
│   ├── scraper.py         # Enhanced scraper with delta detection
│   ├── uploader.py        # Vector store uploader
│   ├── delta_detector.py  # Change detection logic
│   └── storage.py         # State persistence
├── deploy/
│   ├── docker-compose.yml # Local testing
│   └── digitalocean.yml   # DigitalOcean configuration
├── logs/                  # Job execution logs
└── data/                  # State and cache files
```

## Quick Start

### Local Testing

```bash
# Build and run locally
docker build -t daily-scraper .
docker run -e OPENAI_API_KEY=your-key daily-scraper

# Or run directly
python main.py --dry-run
```

### DigitalOcean Deployment

```bash
# Deploy to DigitalOcean
doctl apps create deploy/digitalocean.yml
```

## Delta Detection Strategy

1. **Content Hashing** - SHA256 of article content
2. **Last-Modified Headers** - HTTP header comparison
3. **Metadata Tracking** - Article ID, title, update timestamps
4. **State Persistence** - JSON file with previous run state

## Logging Output

Each run produces logs with:

- **Added**: New articles discovered
- **Updated**: Existing articles with changes
- **Skipped**: Unchanged articles
- **Errors**: Failed operations
- **Summary**: Total counts and execution time

## Environment Variables

### Required

- `OPENAI_API_KEY` - OpenAI API key for vector store operations

### Optional Configuration

- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `DRY_RUN` - Test mode without uploads: true/false (default: false)
- `MAX_ARTICLES` - Limit articles for testing (default: unlimited)
- `REQUEST_DELAY` - Delay between requests in seconds (default: 1.0)
- `MAX_RETRIES` - Maximum retry attempts (default: 3)
- `VECTOR_STORE_NAME` - Name for OpenAI vector store (default: "OptiSigns Support Articles")
- `CHUNK_SIZE` - Maximum chunk size in characters (default: 8000)
- `MIN_CHUNK_SIZE` - Minimum chunk size in characters (default: 100)
- `ENABLE_HASH_DETECTION` - Enable content hash comparison (default: true)
- `ENABLE_LASTMOD_DETECTION` - Enable Last-Modified header detection (default: true)
- `FORCE_FULL_UPDATE` - Force update all articles (default: false)
- `API_RATE_LIMIT` - Delay between API calls in seconds (default: 0.5)
- `BATCH_SIZE` - Number of articles per batch (default: 10)
- `WEBHOOK_URL` - URL for status notifications (optional)
- `ALERT_ON_ERRORS` - Send alerts on errors (default: true)
- `ALERT_THRESHOLD` - Error count threshold for alerts (default: 5)

## Setup Instructions

### 1. Local Development Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd daily-scraper-job

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.sample .env

# Edit .env file with your configuration
# At minimum, set OPENAI_API_KEY
```

### 2. Local Testing

```bash
# Test with dry run (no uploads)
python main.py --dry-run --max-articles 5 --log-level DEBUG

# Run normally (uploads to OpenAI)
python main.py

# Run with custom settings
python main.py --max-articles 10 --log-level INFO
```

### 3. Docker Testing

```bash
# Build the image
docker build -t daily-scraper .

# Run with environment file
docker run --env-file .env daily-scraper

# Run with dry-run mode
docker run -e OPENAI_API_KEY=your-key -e DRY_RUN=true daily-scraper

# Run with docker-compose
cd deploy
docker-compose up
```

### 4. DigitalOcean Deployment

```bash
# Install doctl CLI
# https://docs.digitalocean.com/reference/doctl/how-to/install/

# Authenticate with DigitalOcean
doctl auth init

# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key-here

# Deploy using the script
./deploy.sh

# Or deploy manually
doctl apps create deploy/digitalocean.yml
```

## Monitoring and Logs

### Health Check Endpoints

The application provides several endpoints for monitoring:

- `GET /health` - Basic health check (returns 200 if service is running)
- `GET /status` - Detailed status with job history and metrics
- `GET /metrics` - Prometheus-compatible metrics

### Log Files

Logs are stored in the `logs/` directory:

- `scraper_YYYYMMDD.log` - Daily log files with detailed execution logs
- `scraper_structured_YYYYMMDD.jsonl` - Structured logs in JSON format for monitoring

### Job Artifacts

- `data/scraper_state.json` - Current state with article metadata
- `data/job_history.json` - History of recent job executions
- `data/metrics.json` - Current job metrics
- `data/backups/` - Backup copies of previous states

### Sample Log Output

```
2024-01-15 02:00:01 | INFO     | __main__ | 🚀 Starting daily scraper job
2024-01-15 02:00:01 | INFO     | __main__ | 📂 Loaded state with 45 previous articles
2024-01-15 02:00:02 | INFO     | src.scraper | 🕷️ Starting enhanced article scraping...
2024-01-15 02:00:15 | INFO     | src.scraper | 📄 Found 47 total articles
2024-01-15 02:00:16 | INFO     | __main__ | 🔍 Detecting changes...
2024-01-15 02:00:16 | INFO     | src.delta_detector | 📊 Changes detected: 2 added, 1 updated, 44 unchanged
2024-01-15 02:00:17 | INFO     | __main__ | 📤 Uploading 2 new articles...
2024-01-15 02:00:25 | INFO     | __main__ | 🔄 Updating 1 modified articles...
2024-01-15 02:00:30 | INFO     | __main__ | 📊 Job completed successfully!
2024-01-15 02:00:30 | INFO     | __main__ | ⏱️ Execution time: 29.45 seconds
2024-01-15 02:00:30 | INFO     | __main__ | ➕ Added: 2
2024-01-15 02:00:30 | INFO     | __main__ | 🔄 Updated: 1
2024-01-15 02:00:30 | INFO     | __main__ | ⏭️ Skipped: 44
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Issues**

   ```bash
   # Verify your API key is set
   echo $OPENAI_API_KEY

   # Test API access
   python -c "from openai import OpenAI; print(OpenAI().models.list())"
   ```

2. **Scraping Issues**

   ```bash
   # Test with dry run and debug logging
   python main.py --dry-run --max-articles 1 --log-level DEBUG

   # Check network connectivity
   curl -I https://support.optisigns.com
   ```

3. **Docker Issues**

   ```bash
   # Check container logs
   docker logs <container-id>

   # Run interactively for debugging
   docker run -it --entrypoint /bin/bash daily-scraper
   ```

4. **DigitalOcean Deployment Issues**

   ```bash
   # Check app status
   doctl apps list

   # View deployment logs
   doctl apps logs <app-id>

   # Update configuration
   doctl apps update <app-id> deploy/digitalocean.yml
   ```

### Performance Tuning

- **Reduce API calls**: Increase `API_RATE_LIMIT` for faster execution
- **Batch processing**: Adjust `BATCH_SIZE` based on memory constraints
- **Chunking**: Tune `CHUNK_SIZE` and `MIN_CHUNK_SIZE` for optimal vector store performance
- **Rate limiting**: Adjust `REQUEST_DELAY` to be respectful to the source website

### Monitoring Best Practices

1. **Set up alerts**: Configure `WEBHOOK_URL` for Slack/Discord notifications
2. **Monitor logs**: Use structured logs for automated monitoring
3. **Track metrics**: Use the `/metrics` endpoint with Prometheus
4. **Regular backups**: State files are automatically backed up in `data/backups/`

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ config/ *.py

# Lint code
flake8 src/ config/ *.py

# Type checking (if using mypy)
mypy src/ config/
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests and linting
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the logs in `logs/` directory
3. Check the health endpoints for status information
4. Create an issue in the GitHub repository

## Deliverables Checklist

- ✅ **GitHub repo** with cryptic name (not "optisigns")
- ✅ **Clear commits** with no hard-coded keys (use .env.sample)
- ✅ **Dockerfile** that runs with `docker run -e OPENAI_API_KEY=... main.py`
- ✅ **README** with setup instructions, local run guide, and daily job logs link
- ✅ **Screenshot capability** - Assistant correctly answers sample questions with cited URLs

### Job Logs and Artifacts

- **Live logs**: Available at health check endpoints (`/status`, `/metrics`)
- **Historical logs**: Stored in `logs/` directory with daily rotation
- **Job artifacts**: State files and metrics in `data/` directory
- **Monitoring**: Comprehensive logging with added/updated/skipped counts
