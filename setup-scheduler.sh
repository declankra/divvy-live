#!/bin/bash

# Divvy Live Scheduler Setup
# Sets up Cloud Scheduler jobs for scraper and rollup functions

set -e  # Exit on any error

echo "🕐 Divvy Live - Cloud Scheduler Setup"
echo "====================================="

# Source environment configuration
if [ -f config.env ]; then
    source config.env
    echo "✅ Using environment from config.env"
    echo "   Project: $GCP_PROJECT"
    echo "   Region: $REGION"
else
    echo "❌ config.env not found!"
    echo "   Please copy config.env.template to config.env and update with your values"
    exit 1
fi

# Check if functions exist before setting up scheduler
echo "🔍 Checking if functions are deployed..."

for func in "divvy-scraper" "divvy-rollup"; do
    if ! gcloud functions describe $func --gen2 --region=$REGION --quiet > /dev/null 2>&1; then
        echo "❌ Function $func not found in region $REGION"
        echo "   Please deploy functions first: ./deploy.sh"
        exit 1
    else
        echo "✅ Found $func"
    fi
done

echo ""
echo "🕐 Setting up Cloud Scheduler jobs..."

# Delete existing jobs if they exist (ignore errors)
gcloud scheduler jobs delete divvy-scraper-15 --location=$REGION --quiet 2>/dev/null || true
gcloud scheduler jobs delete divvy-rollup-daily --location=$REGION --quiet 2>/dev/null || true

# Every 15 minutes scraper
echo "Creating scraper job (every 15 minutes)..."
gcloud scheduler jobs create http divvy-scraper-15 \
  --schedule "*/15 * * * *" \
  --uri $(gcloud functions describe divvy-scraper --gen2 --region $REGION --format 'value(serviceConfig.uri)') \
  --http-method GET \
  --time-zone "America/Chicago" \
  --location $REGION

# Daily roll-up at 02:15 AM Central Time
echo "Creating rollup job (daily at 2:15 AM)..."
gcloud scheduler jobs create http divvy-rollup-daily \
  --schedule "15 2 * * *" \
  --uri $(gcloud functions describe divvy-rollup --gen2 --region $REGION --format 'value(serviceConfig.uri)') \
  --http-method GET \
  --time-zone "America/Chicago" \
  --location $REGION

echo ""
echo "✅ Cloud Scheduler jobs created successfully!"
echo ""
echo "📋 Scheduler Summary:"
echo "  • Scraper runs every 15 minutes"
echo "  • Rollup runs daily at 2:15 AM Central Time"
echo ""
echo "🔧 Management commands:"
echo "  View jobs:      gcloud scheduler jobs list --location=$REGION"
echo "  Test scraper:   gcloud scheduler jobs run divvy-scraper-15 --location=$REGION"
echo "  Test rollup:    gcloud scheduler jobs run divvy-rollup-daily --location=$REGION"
echo "  Pause scraper:  gcloud scheduler jobs pause divvy-scraper-15 --location=$REGION"
echo "  Resume scraper: gcloud scheduler jobs resume divvy-scraper-15 --location=$REGION" 