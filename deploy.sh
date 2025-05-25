#!/bin/bash

# Divvy Live Deployment Script
# Deploys all Cloud Functions with proper environment configuration

set -e  # Exit on any error

# Parse command line arguments
SETUP_SCHEDULER=false
if [[ "$1" == "--with-scheduler" ]]; then
    SETUP_SCHEDULER=true
fi

# Source environment configuration
if [ -f config.env ]; then
    source config.env
    echo "✅ Using environment from config.env"
    echo "   Project: $GCP_PROJECT"
    echo "   Bucket: $BUCKET_NAME"
    echo "   Region: $REGION"
else
    echo "❌ config.env not found!"
    echo "   Please copy config.env.template to config.env and update with your values"
    exit 1
fi

# Function to deploy with error handling
deploy_function() {
    local func_name=$1
    local func_dir=$2
    local entry_point=$3
    local memory=$4
    local timeout=$5
    
    echo ""
    echo "🚀 Deploying $func_name..."
    
    gcloud functions deploy $func_name \
        --gen2 --runtime=python312 --region=$REGION \
        --source=./gcp-functions/$func_dir \
        --entry-point=$entry_point \
        --trigger=http --allow-unauthenticated \
        --memory=$memory --timeout=$timeout \
        --set-env-vars=BUCKET_NAME=$BUCKET_NAME,GCP_PROJECT=$GCP_PROJECT \
        --max-instances=10
    
    if [ $? -eq 0 ]; then
        echo "✅ $func_name deployed successfully"
    else
        echo "❌ Failed to deploy $func_name"
        exit 1
    fi
}

echo "🔧 Deploying Divvy Live Cloud Functions"
echo "========================================"

# Deploy all functions
deploy_function "divvy-scraper" "scrapper" "grab" "256MiB" "60s"
deploy_function "divvy-rollup" "rollup" "rollup" "1GiB" "300s"
deploy_function "divvy-api" "api" "latest" "256MiB" "60s"

echo ""
echo "🎉 All functions deployed successfully!"

# Set up scheduler if requested
if [ "$SETUP_SCHEDULER" = true ]; then
    echo ""
    echo "🕐 Setting up Cloud Scheduler..."
    
    # Use the template directly since we already have the environment loaded
    bash commands-setup/gcloud-scheduler.template
fi

echo ""
echo "🎯 Deployment Complete!"
echo ""
echo "Next steps:"
if [ "$SETUP_SCHEDULER" = false ]; then
    echo "1. Set up Cloud Scheduler: ./deploy.sh --with-scheduler (or bash commands-setup/gcloud-scheduler.template)"
else
    echo "1. ✅ Cloud Scheduler already configured"
fi
echo "2. Test the API endpoint: curl https://$REGION-$GCP_PROJECT.cloudfunctions.net/divvy-api"
echo "3. Deploy your website to Vercel"
echo ""
echo "Usage:"
echo "  ./deploy.sh                    # Deploy functions only"
echo "  ./deploy.sh --with-scheduler   # Deploy functions + set up scheduler" 