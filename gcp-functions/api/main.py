import gzip, json, os
from google.cloud import storage
import functions_framework

BUCKET = os.getenv('BUCKET_NAME', 'your-bucket-name')  # Replace with your bucket name
client = storage.Client()

@functions_framework.http
def latest(request):
    # Create a fresh blob reference on each request to avoid caching issues
    blob = client.bucket(BUCKET).blob("aggregated/live_dpi.json.gz")
    raw = blob.download_as_bytes()
    data = json.loads(gzip.decompress(raw))
    return (json.dumps(data), 200, {"Content-Type": "application/json"})
