import os, datetime as dt, duckdb, gzip, json, gcsfs, tempfile
from google.cloud import storage
import pandas as pd
import functions_framework
import pytz

BUCKET = os.getenv('BUCKET_NAME', 'your-bucket-name')  # Replace with your bucket name

@functions_framework.http
def rollup(request):
    """Aggregate last 30 days of snapshots → live_dpi.json.gz."""
    print(f"=== ROLLUP DEBUG START ===")
    print(f"Using bucket: {BUCKET}")
    
    # Initialize gcsfs inside the function to avoid fork-safety issues
    fs = gcsfs.GCSFileSystem(project=os.environ["GCP_PROJECT"])
    client = storage.Client()
    bucket = client.bucket(BUCKET)
    
    # Use Central Time for date calculations to match snapshot folder structure
    central_tz = pytz.timezone('America/Chicago')
    since = dt.datetime.now(central_tz) - dt.timedelta(days=30)
    now = dt.datetime.now(central_tz)
    
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

    # Download files to temporary directory using authenticated gcsfs
    with tempfile.TemporaryDirectory() as temp_dir:
        local_paths = []
        print(f"Downloading {len(filtered_paths)} snapshot files...")
        
        for i, gcs_path in enumerate(filtered_paths):
            local_path = os.path.join(temp_dir, f"snapshot_{i}.json.gz")
            # Download using gcsfs (authenticated)
            with fs.open(gcs_path, 'rb') as src, open(local_path, 'wb') as dst:
                dst.write(src.read())
            local_paths.append(local_path)
        
        # Now use DuckDB with local files
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.sql(f"CREATE TABLE snaps AS SELECT * FROM read_json_auto({local_paths})")
        
        # Debug: Check snapshot data
        snap_count = con.sql("SELECT COUNT(*) FROM snaps").fetchone()[0]
        print(f"Loaded {snap_count} snapshots into DuckDB")
        
        if snap_count > 0:
            # Check if stations array exists and has data
            stations_check = con.sql("SELECT COUNT(*) FROM snaps WHERE json_array_length(stations) > 0").fetchone()[0]
            print(f"Snapshots with non-empty stations array: {stations_check}")

        pct_full = con.sql("""
            SELECT unnest.station_id,
                   AVG((unnest.num_docks_available = 0)::INT) AS pct_full
            FROM snaps
            CROSS JOIN UNNEST(stations) AS unnest
            GROUP BY 1
        """)
        
        # Debug: Check pct_full results
        pct_full_count = con.sql("SELECT COUNT(*) FROM pct_full").fetchone()[0]
        print(f"Stations with pct_full calculated: {pct_full_count}")

        # For historical flows and capacity data, we'll also need to download these
        # since DuckDB will have the same auth issues with these files
        hist_local = os.path.join(temp_dir, "station_flows.parquet")
        cap_local = os.path.join(temp_dir, "station_capacity.csv")
        
        print("Downloading historical data files...")
        
        try:
            # Download historical flows parquet
            with fs.open(f"{BUCKET}/aggregated/station_flows.parquet", 'rb') as src, open(hist_local, 'wb') as dst:
                dst.write(src.read())
            print("✓ Downloaded station_flows.parquet")
        except Exception as e:
            print(f"ERROR downloading station_flows.parquet: {e}")
            return (f"Error: station_flows.parquet not found - {e}", 500)
        
        try:
            # Download capacity CSV
            with fs.open(f"{BUCKET}/station_capacity.csv", 'rb') as src, open(cap_local, 'wb') as dst:
                dst.write(src.read())
            print("✓ Downloaded station_capacity.csv")
        except Exception as e:
            print(f"ERROR downloading station_capacity.csv: {e}")
            return (f"Error: station_capacity.csv not found - {e}", 500)
        
        con.sql(f"CREATE TABLE hist AS SELECT * FROM read_parquet('{hist_local}')")
        con.sql(f"CREATE TABLE cap  AS SELECT * FROM read_csv_auto('{cap_local}')")
        
        # Debug: Check historical data
        hist_count = con.sql("SELECT COUNT(*) FROM hist").fetchone()[0]
        cap_count = con.sql("SELECT COUNT(*) FROM cap").fetchone()[0]
        print(f"Historical flow records: {hist_count}")
        print(f"Capacity records: {cap_count}")
        
        # Debug: Check individual joins before final query
        if pct_full_count > 0 and hist_count > 0 and cap_count > 0:
            hist_cap_join = con.sql("SELECT COUNT(*) FROM hist h JOIN cap c ON h.station_id = c.legacy_id").fetchone()[0]
            print(f"hist + cap join results: {hist_cap_join}")
            
            cap_pct_join = con.sql("SELECT COUNT(*) FROM cap c JOIN pct_full pf ON c.station_id = pf.station_id").fetchone()[0]
            print(f"cap + pct_full join results: {cap_pct_join}")
            
            # Full three-way join
            full_join = con.sql("""
                SELECT COUNT(*) FROM hist h 
                JOIN cap c ON h.station_id = c.legacy_id 
                JOIN pct_full pf ON c.station_id = pf.station_id
            """).fetchone()[0]
            print(f"Full three-way join results: {full_join}")

        res = con.sql("""
            SELECT h.station_id,
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

    # save as compressed JSON for easy fetch from Vercel edge functions
    payload = res.to_dict(orient="records")
    buf = gzip.compress(json.dumps(payload).encode())
    bucket.blob("aggregated/live_dpi.json.gz").upload_from_string(buf, content_type="application/json")

    print(f"=== ROLLUP DEBUG END ===")
    return (f"{len(res)} rows → live_dpi.json.gz", 200)
