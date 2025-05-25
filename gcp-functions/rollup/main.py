import os, datetime as dt, duckdb, gzip, json, gcsfs, tempfile
from google.cloud import storage
import pandas as pd
import functions_framework
import pytz

BUCKET = os.getenv('BUCKET_NAME', 'your-bucket-name')  # Replace with your bucket name

def get_last_processed_timestamp(bucket):
    """Get the last processed timestamp from GCS state file."""
    try:
        blob = bucket.blob("aggregated/rollup_state.txt")
        if blob.exists():
            timestamp_str = blob.download_as_text().strip()
            return dt.datetime.fromisoformat(timestamp_str)
        return None
    except Exception as e:
        print(f"Error reading last processed timestamp: {e}")
        return None

def save_last_processed_timestamp(bucket, timestamp):
    """Save the last processed timestamp to GCS state file."""
    try:
        blob = bucket.blob("aggregated/rollup_state.txt")
        blob.upload_from_string(timestamp.isoformat(), content_type="text/plain")
        print(f"Saved last processed timestamp: {timestamp.isoformat()}")
    except Exception as e:
        print(f"Error saving last processed timestamp: {e}")

def get_snapshots_since(fs, bucket_name, since_timestamp, central_tz):
    """Get snapshot paths since the given timestamp."""
    all_paths = fs.glob(f"{bucket_name}/snapshots/*/*/*/*.json.gz")
    
    if since_timestamp is None:
        # First run - return all paths
        return all_paths
    
    filtered_paths = []
    for path in all_paths:
        try:
            # Extract date and time from path: snapshots/YYYY/MM/DD/HHMMSS.json.gz
            path_parts = path.split('/')
            date_str = "/".join(path_parts[2:5])  # YYYY/MM/DD
            time_str = path_parts[5].replace('.json.gz', '')  # HHMMSS
            
            # Parse the snapshot timestamp
            snapshot_dt = dt.datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H%M%S")
            snapshot_dt = central_tz.localize(snapshot_dt)
            
            if snapshot_dt > since_timestamp:
                filtered_paths.append(path)
        except Exception as e:
            print(f"Error parsing timestamp from path {path}: {e}")
            continue
    
    return filtered_paths

def create_daily_aggregate(con, snapshots_for_date, date_str):
    """Create daily pct_full aggregate for a specific date."""
    if not snapshots_for_date:
        return None
    
    # Calculate pct_full for this date's snapshots
    pct_full_result = con.sql("""
        SELECT unnest.station_id,
               AVG((unnest.num_docks_available = 0)::INT) AS pct_full
        FROM snaps
        CROSS JOIN UNNEST(stations) AS unnest
        GROUP BY 1
    """).df()
    
    if len(pct_full_result) == 0:
        return None
    
    # Convert to dictionary format for JSON storage
    daily_data = {
        "date": date_str,
        "stations": pct_full_result.to_dict('records')
    }
    
    return daily_data

def save_daily_aggregate(bucket, daily_data):
    """Save daily aggregate to GCS."""
    if daily_data is None:
        return
    
    date_str = daily_data["date"]
    blob_path = f"aggregated/daily_pct_full/{date_str}.json"
    
    try:
        blob = bucket.blob(blob_path)
        blob.upload_from_string(json.dumps(daily_data), content_type="application/json")
        print(f"Saved daily aggregate for {date_str}")
    except Exception as e:
        print(f"Error saving daily aggregate for {date_str}: {e}")

def load_daily_aggregates(fs, bucket_name, days=30):
    """Load the last N days of daily aggregates."""
    central_tz = pytz.timezone('America/Chicago')
    end_date = dt.datetime.now(central_tz).date()
    start_date = end_date - dt.timedelta(days=days-1)
    
    all_station_data = []
    
    for i in range(days):
        current_date = start_date + dt.timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        blob_path = f"{bucket_name}/aggregated/daily_pct_full/{date_str}.json"
        
        try:
            with fs.open(blob_path, 'r') as f:
                daily_data = json.load(f)
                all_station_data.extend(daily_data["stations"])
        except Exception as e:
            print(f"Daily aggregate not found for {date_str}: {e}")
            continue
    
    if not all_station_data:
        return None
    
    # Convert to DataFrame and calculate average pct_full across all days
    df = pd.DataFrame(all_station_data)
    if len(df) == 0:
        return None
    
    # Group by station_id and average the pct_full values
    result = df.groupby('station_id')['pct_full'].mean().reset_index()
    return result

def should_use_incremental_processing(fs, bucket_name):
    """Determine if we should use incremental processing or full processing."""
    central_tz = pytz.timezone('America/Chicago')
    
    # Check how many days of data we have
    try:
        all_paths = fs.glob(f"{bucket_name}/snapshots/*/*/*/*.json.gz")
        if len(all_paths) == 0:
            return False
        
        # Get the earliest snapshot date
        earliest_date = None
        for path in all_paths:
            try:
                path_parts = path.split('/')
                date_str = "/".join(path_parts[2:5])  # YYYY/MM/DD
                snapshot_date = dt.datetime.strptime(date_str, "%Y/%m/%d").date()
                if earliest_date is None or snapshot_date < earliest_date:
                    earliest_date = snapshot_date
            except:
                continue
        
        if earliest_date is None:
            return False
        
        # If we have less than 3 days of data, use full processing
        days_of_data = (dt.datetime.now(central_tz).date() - earliest_date).days
        return days_of_data >= 3
        
    except Exception as e:
        print(f"Error checking data age: {e}")
        return False

@functions_framework.http
def rollup(request):
    """Aggregate snapshots → live_dpi.json.gz with incremental processing."""
    print(f"=== ROLLUP DEBUG START ===")
    print(f"Using bucket: {BUCKET}")
    
    # Initialize gcsfs and storage client
    fs = gcsfs.GCSFileSystem(project=os.environ["GCP_PROJECT"])
    client = storage.Client()
    bucket = client.bucket(BUCKET)
    
    # Use Central Time for date calculations
    central_tz = pytz.timezone('America/Chicago')
    now = dt.datetime.now(central_tz)
    
    # Check if we should use incremental processing
    use_incremental = should_use_incremental_processing(fs, BUCKET)
    print(f"Using incremental processing: {use_incremental}")
    
    if use_incremental:
        # Get last processed timestamp
        last_processed = get_last_processed_timestamp(bucket)
        print(f"Last processed timestamp: {last_processed}")
        
        # Get snapshots since last processing
        new_snapshot_paths = get_snapshots_since(fs, BUCKET, last_processed, central_tz)
        print(f"New snapshots to process: {len(new_snapshot_paths)}")
        
        if new_snapshot_paths:
            # Process new snapshots and create/update daily aggregates
            with tempfile.TemporaryDirectory() as temp_dir:
                # Group snapshots by date
                snapshots_by_date = {}
                local_paths = []
                
                for i, gcs_path in enumerate(new_snapshot_paths):
                    # Extract date from path
                    path_parts = gcs_path.split('/')
                    date_str = "-".join(path_parts[2:5])  # YYYY-MM-DD
                    
                    if date_str not in snapshots_by_date:
                        snapshots_by_date[date_str] = []
                    
                    # Download snapshot
                    local_path = os.path.join(temp_dir, f"snapshot_{i}.json.gz")
                    with fs.open(gcs_path, 'rb') as src, open(local_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    snapshots_by_date[date_str].append(local_path)
                    local_paths.append(local_path)
                
                # Process each date's snapshots
                con = duckdb.connect()
                con.execute("INSTALL httpfs; LOAD httpfs;")
                
                for date_str, date_paths in snapshots_by_date.items():
                    print(f"Processing {len(date_paths)} snapshots for {date_str}")
                    
                    # Load snapshots for this date
                    con.sql(f"DROP TABLE IF EXISTS snaps")
                    con.sql(f"CREATE TABLE snaps AS SELECT * FROM read_json_auto({date_paths})")
                    
                    # Create daily aggregate
                    daily_data = create_daily_aggregate(con, date_paths, date_str)
                    save_daily_aggregate(bucket, daily_data)
        
        # Load daily aggregates for DPI calculation
        pct_full_df = load_daily_aggregates(fs, BUCKET, days=30)
        
        if pct_full_df is None:
            print("No daily aggregates found, falling back to full processing")
            use_incremental = False
    
    if not use_incremental:
        # Full processing (original logic)
        print("Using full processing mode")
        since = now - dt.timedelta(days=30)
        print(f"Date range: {since.date()} to {now.date()}")
        
        paths = fs.glob(f"{BUCKET}/snapshots/*/*/*/*.json.gz")
        print(f"Total snapshot files found: {len(paths)}")
        
        filtered_paths = [
            p for p in paths
            if dt.datetime.strptime("/".join(p.split('/')[2:5]), "%Y/%m/%d").date() >= since.date()
        ]
        
        print(f"Filtered snapshot files (last 30 days): {len(filtered_paths)}")
        
        if not filtered_paths:
            print("ERROR: No snapshots found in date range")
            return ("no snapshots", 200)

        # Download and process all snapshots
        with tempfile.TemporaryDirectory() as temp_dir:
            local_paths = []
            print(f"Downloading {len(filtered_paths)} snapshot files...")
            
            for i, gcs_path in enumerate(filtered_paths):
                local_path = os.path.join(temp_dir, f"snapshot_{i}.json.gz")
                with fs.open(gcs_path, 'rb') as src, open(local_path, 'wb') as dst:
                    dst.write(src.read())
                local_paths.append(local_path)
            
            # Calculate pct_full from all snapshots
            con = duckdb.connect()
            con.execute("INSTALL httpfs; LOAD httpfs;")
            con.sql(f"CREATE TABLE snaps AS SELECT * FROM read_json_auto({local_paths})")
            
            pct_full_result = con.sql("""
                SELECT unnest.station_id,
                       AVG((unnest.num_docks_available = 0)::INT) AS pct_full
                FROM snaps
                CROSS JOIN UNNEST(stations) AS unnest
                GROUP BY 1
            """)
            
            pct_full_df = pct_full_result.df()
    
    # Continue with DPI calculation (same for both modes)
    if len(pct_full_df) == 0:
        print("ERROR: No pct_full data calculated")
        return ("no pct_full data", 500)
    
    print(f"Stations with pct_full calculated: {len(pct_full_df)}")
    
    # Download historical data files
    with tempfile.TemporaryDirectory() as temp_dir:
        hist_local = os.path.join(temp_dir, "station_flows.parquet")
        cap_local = os.path.join(temp_dir, "station_capacity.csv")
        
        print("Downloading historical data files...")
        
        try:
            with fs.open(f"{BUCKET}/aggregated/station_flows.parquet", 'rb') as src, open(hist_local, 'wb') as dst:
                dst.write(src.read())
            print("✓ Downloaded station_flows.parquet")
        except Exception as e:
            print(f"ERROR downloading station_flows.parquet: {e}")
            return (f"Error: station_flows.parquet not found - {e}", 500)
        
        try:
            with fs.open(f"{BUCKET}/station_capacity.csv", 'rb') as src, open(cap_local, 'wb') as dst:
                dst.write(src.read())
            print("✓ Downloaded station_capacity.csv")
        except Exception as e:
            print(f"ERROR downloading station_capacity.csv: {e}")
            return (f"Error: station_capacity.csv not found - {e}", 500)
        
        # Load historical data into DuckDB
        con = duckdb.connect()
        con.sql(f"CREATE TABLE hist AS SELECT * FROM read_parquet('{hist_local}')")
        con.sql(f"CREATE TABLE cap  AS SELECT * FROM read_csv_auto('{cap_local}')")
        
        # Load pct_full data into DuckDB
        con.register('pct_full_df', pct_full_df)
        con.sql("CREATE TABLE pct_full AS SELECT * FROM pct_full_df")
        
        # Debug: Check data counts
        hist_count = con.sql("SELECT COUNT(*) FROM hist").fetchone()[0]
        cap_count = con.sql("SELECT COUNT(*) FROM cap").fetchone()[0]
        pct_full_count = con.sql("SELECT COUNT(*) FROM pct_full").fetchone()[0]
        print(f"Historical flow records: {hist_count}")
        print(f"Capacity records: {cap_count}")
        print(f"Pct_full records: {pct_full_count}")
        
        # Calculate final DPI
        res = con.sql("""
            SELECT h.station_id,
                   cap.name                                             AS station_name,
                   ROUND((h.ends - h.starts)::FLOAT / cap.capacity, 3)   AS overflow_per_dock,
                   ROUND(pf.pct_full, 3)                                AS pct_full,
                   ROUND((h.ends - h.starts)::FLOAT / cap.capacity * pf.pct_full, 3) AS dpi
            FROM hist h 
            JOIN cap ON h.station_id = cap.legacy_id 
            JOIN pct_full pf ON cap.station_id = pf.station_id
            ORDER BY dpi DESC
        """).df()
        
        print(f"Final DPI results: {len(res)} rows")
        if len(res) > 0:
            print(f"Top 3 DPI stations: {res.head(3).to_dict('records')}")

    # Save results
    payload = res.to_dict(orient="records")
    buf = gzip.compress(json.dumps(payload).encode())
    bucket.blob("aggregated/live_dpi.json.gz").upload_from_string(buf, content_type="application/json")
    
    # Update last processed timestamp
    save_last_processed_timestamp(bucket, now)
    
    print(f"=== ROLLUP DEBUG END ===")
    return (f"{len(res)} rows → live_dpi.json.gz", 200)
