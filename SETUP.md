# Divvy Live Setup Guide

This guide helps you set up your own instance of the Divvy Live dashboard.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and authenticated
- `gsutil` installed
- Python 3.12+
- Node.js 18+

## 1. Environment Configuration

### Quick Setup (Recommended)
1. Copy the environment template:
   ```bash
   cp config.env.template config.env
   ```
2. Edit `config.env` with your actual values:
   ```bash
   export BUCKET_NAME="divvy-live-your-region"
   export GCP_PROJECT="your-actual-project-id"
   export REGION="us-central1"
   ```

### Manual Setup (Alternative)
1. Copy individual templates:
   ```bash
   cp commands-setup/gcloud-prereqs.template commands-setup/gcloud-prereqs
   cp commands-setup/gcloud-deploy-rollup.template commands-setup/gcloud-deploy-rollup
   cp commands-setup/gcloud-deploy-api.template commands-setup/gcloud-deploy-api
   ```
2. Replace placeholders in each file with your actual values

## 2. Google Cloud Setup

### Configure Your Project
Run: `bash commands-setup/gcloud-prereqs` (or source config.env first)

### Create Storage Bucket
Run: `bash commands-setup/gcloud-bucket`

## 3. Data Preparation

### Historical Data Processing
Run the historical data pipeline:
```bash
cd data-prep
bash download_historical_trips.sh
python process_trips.py
bash export-and-upload.sh
```

### Station Capacity Data
Run: `python data-prep/get_station_capacity.py`

## 4. Deploy Cloud Functions

### One-Command Deployment (Recommended)
```bash
./deploy.sh
```

### Manual Deployment (Alternative)
```bash
bash commands-setup/gcloud-deploy-scraper
bash commands-setup/gcloud-deploy-rollup  
bash commands-setup/gcloud-deploy-api
```

### Schedule Functions

#### One-Command Setup (Recommended)
```bash
./deploy.sh --with-scheduler
```

#### Standalone Scheduler Setup
```bash
./setup-scheduler.sh
```

#### Manual Setup (Alternative)
```bash
bash commands-setup/gcloud-scheduler.template
```

#### Managing Scheduled Jobs
```bash
# View current jobs
source config.env
gcloud scheduler jobs list --location=$REGION

# Test jobs manually
gcloud scheduler jobs run divvy-scraper-15 --location=$REGION
gcloud scheduler jobs run divvy-rollup-daily --location=$REGION

# Pause/resume jobs
gcloud scheduler jobs pause divvy-scraper-15 --location=$REGION
gcloud scheduler jobs resume divvy-scraper-15 --location=$REGION
```

## 5. Deploy Website

### Vercel Deployment
1. Fork this repository
2. Connect to Vercel
3. Vercel will automatically detect the `vercel.json` configuration
4. The website deploys from the `website-reporting/` folder

### Configure API Endpoint
Edit `website-reporting/src/app/api/dpi/route.ts` and update the Cloud Function URL with your project details.

## Continuous Development

### Making Changes and Redeploying
1. Make your changes to the function code
2. Run `./deploy.sh` to redeploy all functions
3. Environment variables are automatically sourced from `config.env`

### Individual Function Deployment
You can also deploy individual functions:
```bash
source config.env
gcloud functions deploy divvy-api --source=./gcp-functions/api --entry-point=latest --trigger=http --set-env-vars=BUCKET_NAME=$BUCKET_NAME,GCP_PROJECT=$GCP_PROJECT
```

## Environment Variables

The following environment variables are used by the Cloud Functions:
- `BUCKET_NAME`: Your GCS bucket name
- `GCP_PROJECT`: Your GCP project ID
- `REGION`: Your deployment region

These are set automatically from `config.env` during deployment.

## Security Notes

- Never commit `config.env` - it contains your actual credentials
- Use `config.env.template` as reference for new setups
- The `.gitignore` excludes files with real credentials
- Service account authentication is handled automatically by Cloud Functions 