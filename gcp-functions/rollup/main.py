import os, datetime as dt, duckdb, gzip, json, gcsfs, tempfile
from google.cloud import storage
import pandas as pd
import functions_framework
import pytz

BUCKET = "divvy-live-us-central1"

@functions_framework.http
def rollup(request):
    """Aggregate last 30 days of snapshots → live_dpi.json.gz."""
    # Initialize gcsfs inside the function to avoid fork-safety issues
    fs = gcsfs.GCSFileSystem(project=os.environ["GCP_PROJECT"])
    client = storage.Client()
    bucket = client.bucket(BUCKET)
    
    # Use Central Time for date calculations to match snapshot folder structure
    central_tz = pytz.timezone('America/Chicago')
    since = dt.datetime.now(central_tz) - dt.timedelta(days=30)
    
    paths = fs.glob(f"{BUCKET}/snapshots/*/*/*/*.json.gz")
    filtered_paths = [
        p for p in paths
        if dt.datetime.strptime("/".join(p.split('/')[2:5]), "%Y/%m/%d").date() >= since.date()
    ]
    if not filtered_paths:
        return ("no snapshots", 200)

    # Download files to temporary directory using authenticated gcsfs
    with tempfile.TemporaryDirectory() as temp_dir:
        local_paths = []
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

        pct_full = con.sql("""
            SELECT unnest.station_id,
                   AVG((unnest.num_docks_available = 0)::INT) AS pct_full
            FROM snaps
            CROSS JOIN UNNEST(stations) AS unnest
            GROUP BY 1
        """)

        # For historical flows and capacity data, we'll also need to download these
        # since DuckDB will have the same auth issues with these files
        hist_local = os.path.join(temp_dir, "station_flows.parquet")
        cap_local = os.path.join(temp_dir, "station_capacity.csv")
        
        # Download historical flows parquet
        with fs.open(f"{BUCKET}/aggregated/station_flows.parquet", 'rb') as src, open(hist_local, 'wb') as dst:
            dst.write(src.read())
        
        # Download capacity CSV
        with fs.open(f"{BUCKET}/station_capacity.csv", 'rb') as src, open(cap_local, 'wb') as dst:
            dst.write(src.read())
        
        con.sql(f"CREATE TABLE hist AS SELECT * FROM read_parquet('{hist_local}')")
        con.sql(f"CREATE TABLE cap  AS SELECT * FROM read_csv_auto('{cap_local}')")

        res = con.sql("""
            SELECT h.station_id,
                   ROUND((h.ends - h.starts)::FLOAT / cap.capacity, 3)   AS overflow_per_dock,
                   ROUND(pf.pct_full, 3)                                AS pct_full,
                   ROUND((h.ends - h.starts)::FLOAT / cap.capacity * pf.pct_full, 3) AS dpi
            FROM hist h JOIN cap USING(station_id) JOIN pct_full pf USING(station_id)
            ORDER BY dpi DESC
        """).df()

    # save as compressed JSON for easy fetch from Vercel edge functions
    payload = res.to_dict(orient="records")
    buf = gzip.compress(json.dumps(payload).encode())
    bucket.blob("aggregated/live_dpi.json.gz").upload_from_string(buf, content_type="application/json")

    return (f"{len(res)} rows → live_dpi.json.gz", 200)
