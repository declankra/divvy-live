import json, gzip, io, datetime as dt, requests, functions_framework
from google.cloud import storage
import pytz

BUCKET = "divvy-live-us-central1"
FEED   = "https://gbfs.divvybikes.com/gbfs/en/station_status.json"
client = storage.Client()
bucket = client.bucket(BUCKET)

@functions_framework.http
def grab(request):
    # Use Central Time for folder structure to match local timezone
    central_tz = pytz.timezone('America/Chicago')
    ts_central = dt.datetime.now(central_tz)
    # Keep UTC timestamp for the data itself for consistency
    ts_utc = dt.datetime.now(dt.timezone.utc)
    
    data = requests.get(FEED, timeout=10).json()["data"]["stations"]

    # Use Central Time for folder structure
    blob = bucket.blob(f"snapshots/{ts_central:%Y/%m/%d}/{ts_central:%H%M%S}.json.gz")
    buf  = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="w") as gz:
        # Store UTC timestamp in the data for consistency across timezones
        gz.write(json.dumps({"timestamp": ts_utc.isoformat(), "stations": data}).encode())
    buf.seek(0)
    blob.upload_from_file(buf, content_type="application/json")

    return f"saved {blob.name}", 200
