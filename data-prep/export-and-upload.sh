#!/bin/bash

# ==============================================================================
# Export and Upload Station Flows Data
# ==============================================================================
# 
# Purpose: 
#   Exports the aggregated station flows data from a local DuckDB database
#   to Parquet format and uploads it to Google Cloud Storage for use by
#   the Divvy Live dashboard project.
#
# What it does:
#   1. Exports 'station_flows' table from data-prep/flows.duckdb to station_flows.parquet
#   2. Uploads the Parquet file to gs://YOUR_BUCKET_NAME/aggregated/
#   3. Optionally cleans up local files
#
# Prerequisites:
#   - DuckDB CLI installed and accessible in PATH
#   - Google Cloud SDK (gsutil) installed and authenticated 
#   - data-prep/flows.duckdb file exists with 'station_flows' table
#     (created by running: python3 data-prep/process_trips.py)
#
# Usage:
#   bash data-prep/export-and-upload.sh
#
# Input: data-prep/flows.duckdb (DuckDB database with station_flows table)
# Output: Uploads station_flows.parquet to Google Cloud Storage bucket
#
# Part of: Divvy Live Dashboard - Step 3c (Export & upload to Google Cloud)
# ==============================================================================

# to execute: bash data-prep/export-and-upload.sh

# CONFIGURATION: Update these with your actual values
BUCKET_NAME="YOUR_BUCKET_NAME"  # Replace with your actual bucket name

# Export the DuckDB database to a Parquet file
duckdb data-prep/flows.duckdb "COPY station_flows TO 'data-prep/station_flows.parquet' (FORMAT parquet);"

# Upload the Parquet file to the Google Cloud Storage bucket
gsutil cp data-prep/station_flows.parquet gs://$BUCKET_NAME/aggregated/

# Clean up the local file (consider if you want to keep the parquet locally too)
# rm data-prep/station_flows.parquet
# rm data-prep/flows.duckdb # Optionally clean up the duckdb file too
