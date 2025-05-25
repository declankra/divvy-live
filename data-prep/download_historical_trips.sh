#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- How to Use This Script ---
#
# Purpose:
#   Downloads the last 12 full months of Divvy bike trip data as CSV files.
#   For example, if run in May 2025, it will download data from May 2024 to April 2025.
#   It fetches data from: https://divvy-tripdata.s3.amazonaws.com/
#
# Prerequisites:
#   - curl: For downloading files.
#   - unzip: For extracting zip archives.
#   - date (macOS/BSD compatible): For date calculations.
#
# Setup:
#   1. Make the script executable (run this once from the project root):
#      chmod +x data-prep/download_historical_trips.sh
#
# Running the Script:
#   - Option 1: Navigate to the data-prep directory and run:
#       cd data-prep
#       ./download_historical_trips.sh
#
#   - Option 2: Run from the project root directory:
#       ./data-prep/download_historical_trips.sh
#
# Output:
#   - CSV files will be saved in a subdirectory named "historical_trip_data_csvs"
#     within the "data-prep" directory (e.g., data-prep/historical_trip_data_csvs/).
#   - The script will skip downloading files that already exist in the output directory.
#
# --- Script Start ---

# Define the directory where data will be downloaded and extracted
# This script is intended to be in data-prep/
# It will create a subdirectory historical_trip_data_csvs/ inside data-prep/
OUTPUT_DIR_NAME="historical_trip_data_csvs"
# Get the directory where the script itself is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/${OUTPUT_DIR_NAME}"

mkdir -p "${OUTPUT_DIR}"

echo "Downloading Divvy trip data for the last 12 months to ${OUTPUT_DIR}..."

# Loop for the last 12 months (from 11 months ago to current month)
for i in $(seq 12 -1 1); do
  # Calculate year and month for the iteration
  # On macOS/BSD, -v-Nm adjusts by N months. -v-11m is 11 months ago, -v-0m is current month.
  year_month_process=$(date -v-${i}m "+%Y%m")
  
  m=$year_month_process
  zip_filename="${m}-divvy-tripdata.zip"
  csv_filename="${m}-divvy-tripdata.csv" # Expected CSV filename inside the zip
  s3_url="https://divvy-tripdata.s3.amazonaws.com/${zip_filename}"
  
  echo # Newline for better readability between months
  echo "Processing data for ${m}..."
  
  # Check if CSV file already exists in the output directory to avoid re-processing
  if [ -f "${OUTPUT_DIR}/${csv_filename}" ]; then
    echo "${csv_filename} already exists in ${OUTPUT_DIR}. Skipping."
    continue
  fi
  
  # Check if zip file already exists in the output directory (e.g., from a previous failed unzip)
  if [ -f "${OUTPUT_DIR}/${zip_filename}" ]; then
    echo "${zip_filename} already downloaded in ${OUTPUT_DIR}. Will attempt to unzip."
  else
    echo "Downloading ${zip_filename} from ${s3_url} to ${OUTPUT_DIR}..."
    # Use curl's -L to follow redirects and -o to specify output file path
    # Add --fail to make curl exit with an error on server errors (e.g., 404)
    curl --fail -L -o "${OUTPUT_DIR}/${zip_filename}" "${s3_url}"
    if [ $? -ne 0 ]; then
      echo "Failed to download ${zip_filename}. It might not be available yet or there was an error."
      # Attempt to remove potentially incomplete zip file
      rm -f "${OUTPUT_DIR}/${zip_filename}"
      continue # Try next month
    fi
  fi
  
  # Unzip the file if download was successful (or zip already existed) and zip file exists
  if [ -f "${OUTPUT_DIR}/${zip_filename}" ]; then
    echo "Unzipping ${zip_filename} into ${OUTPUT_DIR}..."
    # Unzip specifically to the OUTPUT_DIR and overwrite if necessary
    # The -d option for unzip specifies the directory.
    # Add -x to exclude macOS specific metadata files.
    unzip -o "${OUTPUT_DIR}/${zip_filename}" -d "${OUTPUT_DIR}" -x "__MACOSX/*" "*/.DS_Store"
    if [ $? -ne 0 ]; then
      echo "Failed to unzip ${zip_filename}."
      # Don't remove the zip if unzip failed, user might want to inspect it
    else
      echo "Successfully unzipped ${zip_filename}."
      # Remove the zip file after successful extraction
      echo "Removing ${zip_filename}..."
      rm "${OUTPUT_DIR}/${zip_filename}"
    fi
  else
    # This case should ideally not be reached if curl succeeded and didn't error out.
    echo "Zip file ${OUTPUT_DIR}/${zip_filename} not found for unzipping. Skipping."
  fi
done

echo # Final newline
echo "Data download and extraction complete. CSV files are in ${OUTPUT_DIR}."
echo "If any months failed, they might not be available on the server yet." 