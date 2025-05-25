import gzip, json, os
from google.cloud import storage
import functions_framework

BUCKET = os.getenv('BUCKET_NAME', 'your-bucket-name')  # Replace with your bucket name
client = storage.Client()
blob   = client.bucket(BUCKET).blob("aggregated/live_dpi.json.gz")

@functions_framework.http
def latest(request):
    raw = blob.download_as_bytes()
    data = json.loads(gzip.decompress(raw))
    return (json.dumps(data), 200, {"Content-Type": "application/json"})
