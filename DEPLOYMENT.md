# Divvy Live Deployment Workflow

Quick reference for deploying and managing your Divvy Live instance.

## 🚀 Initial Setup

```bash
# 1. Configure environment
cp config.env.template config.env
# Edit config.env with your actual values

# 2. Deploy everything at once
./deploy.sh --with-scheduler

# 3. Deploy website to Vercel (see SETUP.md)
```

## 🔄 Development Workflow

### Making Code Changes
```bash
# Make your changes to function code
vim gcp-functions/api/main.py

# Redeploy (uses your config.env automatically)
./deploy.sh
```

### Scheduler Management
```bash
# Update scheduler only
./setup-scheduler.sh

# View current jobs
source config.env && gcloud scheduler jobs list --location=$REGION

# Test functions manually
gcloud scheduler jobs run divvy-scraper-15 --location=$REGION
gcloud scheduler jobs run divvy-rollup-daily --location=$REGION
```

### Individual Function Deployment
```bash
source config.env

# Deploy just the API function
gcloud functions deploy divvy-api \
  --gen2 --runtime=python312 --region=$REGION \
  --source=./gcp-functions/api \
  --entry-point=latest \
  --trigger=http --allow-unauthenticated \
  --set-env-vars=BUCKET_NAME=$BUCKET_NAME,GCP_PROJECT=$GCP_PROJECT
```

## 🔍 Testing & Monitoring

```bash
# Test API endpoint
source config.env
curl "https://$REGION-$GCP_PROJECT.cloudfunctions.net/divvy-api"

# View function logs
gcloud functions logs read divvy-api --gen2 --region=$REGION

# Check scheduler status
gcloud scheduler jobs list --location=$REGION
```

## 📁 File Organization

```
config.env.template    # Template - commit to repo
config.env            # Your actual values - never commit!
deploy.sh             # Main deployment script
setup-scheduler.sh    # Scheduler-only setup
commands-setup/*.template # Templates for individual commands
```

## 🔒 Security Notes

- **Never commit `config.env`** - it contains your actual credentials
- All `*.template` files are safe to commit
- Use templates as reference for new environments
- Environment variables are passed to functions during deployment
``` 