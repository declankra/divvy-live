#!/usr/bin/env python3
"""
Helper script to fetch station capacity and metadata from GBFS station_information.json
This generates station_capacity.csv that gets used by the rollup function.

Usage: python3 get_station_capacity.py
"""

import requests
import csv
import os
import json
from datetime import datetime

def fetch_station_capacity():
    """Fetch station information from GBFS API and save to CSV."""
    
    print("Fetching station information from GBFS API...")
    url = "https://gbfs.divvybikes.com/gbfs/en/station_information.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()["data"]["stations"]
        
        print(f"Found {len(data)} stations")
        
        # Create output filename
        output_file = "station_capacity.csv"
        
        with open(output_file, "w", newline="") as f:
            fieldnames = ["station_id", "name", "lat", "lon", "capacity"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write each station's data
            for station in data:
                writer.writerow({
                    k: station[k] for k in fieldnames
                })
        
        print(f"✅ Successfully created {output_file}")
        print(f"📊 Contains {len(data)} stations with capacity information")
        
        # Show a sample of the data
        print("\nSample of first 3 stations:")
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 3:
                    break
                print(f"  {row['station_id']}: {row['name']} (capacity: {row['capacity']})")
        
        return output_file
        
    except requests.RequestException as e:
        print(f"❌ Error fetching data from GBFS API: {e}")
        return None
    except KeyError as e:
        print(f"❌ Error parsing GBFS response: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def main():
    """Main function to run the capacity fetching process."""
    print("🚲 Divvy Station Capacity Fetcher")
    print("=" * 40)
    
    output_file = fetch_station_capacity()
    
    if output_file:
        print(f"\n✅ Process completed successfully!")
        print(f"📁 Output file: {output_file}")
        print(f"\nNext steps:")
        print(f"  1. Review the generated {output_file}")
        print(f"  2. Upload to GCS: gsutil cp {output_file} gs://YOUR_BUCKET_NAME/")
    else:
        print("\n❌ Process failed. Please check the errors above.")

if __name__ == "__main__":
    main() 