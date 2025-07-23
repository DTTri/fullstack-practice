#!/bin/bash

# Deploy script for DigitalOcean Platform

set -e

echo "🚀 Deploying OptiSigns Daily Scraper to DigitalOcean..."

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl CLI is not installed. Please install it first:"
    echo "   https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if user is authenticated
if ! doctl auth list &> /dev/null; then
    echo "❌ Not authenticated with DigitalOcean. Please run:"
    echo "   doctl auth init"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable is required"
    echo "   Please set it before deploying:"
    echo "   export OPENAI_API_KEY=your-api-key"
    exit 1
fi

# Update the DigitalOcean configuration with the API key
echo "🔧 Updating configuration..."
sed -i.bak "s/your-openai-api-key/$OPENAI_API_KEY/g" deploy/digitalocean.yml

# Get GitHub repo info (if available)
if git remote get-url origin &> /dev/null; then
    REPO_URL=$(git remote get-url origin)
    REPO_NAME=$(basename "$REPO_URL" .git)
    REPO_OWNER=$(basename "$(dirname "$REPO_URL")")
    
    echo "📦 Detected GitHub repo: $REPO_OWNER/$REPO_NAME"
    
    # Update repo info in config
    sed -i.bak "s/your-username\/your-repo-name/$REPO_OWNER\/$REPO_NAME/g" deploy/digitalocean.yml
else
    echo "⚠️  No Git remote found. Please update the GitHub repo info in deploy/digitalocean.yml"
fi

# Deploy to DigitalOcean
echo "🚀 Deploying to DigitalOcean..."
doctl apps create deploy/digitalocean.yml

echo "✅ Deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Check deployment status: doctl apps list"
echo "2. View logs: doctl apps logs <app-id>"
echo "3. Update environment variables in DigitalOcean dashboard if needed"
echo "4. Monitor job execution through the health check endpoints"
echo ""
echo "🔗 Useful commands:"
echo "   doctl apps list                    # List all apps"
echo "   doctl apps get <app-id>           # Get app details"
echo "   doctl apps logs <app-id>          # View logs"
echo "   doctl apps update <app-id> deploy/digitalocean.yml  # Update app"

# Restore original config file
mv deploy/digitalocean.yml.bak deploy/digitalocean.yml
