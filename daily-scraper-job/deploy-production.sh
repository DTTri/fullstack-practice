#!/bin/bash

# Production Deployment Script for Daily Scraper Job
# Deploys to DigitalOcean App Platform with scheduled job

set -e

echo "DEPLOYING DAILY SCRAPER JOB TO DIGITALOCEAN"
echo "==========================================="

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v doctl &> /dev/null; then
    echo "ERROR: doctl CLI not found. Install it first:"
    echo "   https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

if ! doctl auth list &> /dev/null; then
    echo "ERROR: Not authenticated with DigitalOcean. Run:"
    echo "   doctl auth init"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable not set"
    echo "   Set it with: export OPENAI_API_KEY=your-key"
    exit 1
fi

echo "Prerequisites check passed"

# Build Docker image locally for testing
echo ""
echo "Building Docker image for testing..."
docker build -t daily-scraper:latest .

# Test the image locally first
echo ""
echo "Testing Docker image locally..."
docker run --rm -e OPENAI_API_KEY="$OPENAI_API_KEY" -e DRY_RUN=true daily-scraper:latest

echo ""
echo "Local test passed"

# Deploy to DigitalOcean App Platform
echo ""
echo "Deploying to DigitalOcean App Platform..."

APP_NAME="optisigns-daily-scraper-prod"

# Check if app exists
if doctl apps list --format Name --no-header | grep -q "^$APP_NAME$"; then
    echo "Updating existing app: $APP_NAME"
    APP_ID=$(doctl apps list --format ID,Name --no-header | grep "$APP_NAME" | awk '{print $1}')
    doctl apps update $APP_ID --spec deploy/digitalocean-production.yml
else
    echo "Creating new app: $APP_NAME"
    doctl apps create --spec deploy/digitalocean-production.yml
fi

# Get app info
APP_ID=$(doctl apps list --format ID,Name --no-header | grep "$APP_NAME" | awk '{print $1}')

echo ""
echo "DEPLOYMENT COMPLETE!"
echo "==================="
echo "App ID: $APP_ID"
echo "App Name: $APP_NAME"
echo ""
echo "IMPORTANT: Set your OPENAI_API_KEY in DigitalOcean dashboard:"
echo "1. Go to: https://cloud.digitalocean.com/apps/$APP_ID/settings"
echo "2. Navigate to 'Environment Variables'"
echo "3. Set OPENAI_API_KEY as a SECRET with your actual API key"
echo ""
echo "Monitor your deployment:"
echo "  doctl apps list"
echo "  doctl apps logs $APP_ID --follow"
echo "  doctl apps get $APP_ID"
echo ""
echo "The job will run daily at 2:00 AM UTC"
echo "Logs will be available at the dashboard service URL"

# Create a simple monitoring script
cat > monitor-job.sh << 'EOF'
#!/bin/bash
# Monitor the daily scraper job

APP_NAME="optisigns-daily-scraper-prod"
APP_ID=$(doctl apps list --format ID,Name --no-header | grep "$APP_NAME" | awk '{print $1}')

if [ -z "$APP_ID" ]; then
    echo "App not found: $APP_NAME"
    exit 1
fi

echo "Monitoring Daily Scraper Job"
echo "============================"
echo "App ID: $APP_ID"
echo ""

# Show app status
echo "App Status:"
doctl apps get $APP_ID --format ID,Name,Status,CreatedAt,UpdatedAt

echo ""
echo "Recent Logs:"
doctl apps logs $APP_ID --tail 50

echo ""
echo "To follow logs in real-time:"
echo "  doctl apps logs $APP_ID --follow"
EOF

chmod +x monitor-job.sh

echo ""
echo "Created monitoring script: ./monitor-job.sh"
echo "Run it to check job status and logs"
