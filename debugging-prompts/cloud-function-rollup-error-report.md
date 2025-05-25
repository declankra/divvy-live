# Cloud Function Rollup Error Report

## Current Error
The `divvy-rollup` Cloud Function is failing with **HTTP 403 errors** when DuckDB attempts to read snapshot files directly from Google Cloud Storage via HTTPS URLs.

**Specific Error:**
```
duckdb.duckdb.HTTPException: HTTP Error: HTTP GET error on 'https://storage.googleapis.com/divvy-live-us-central1/snapshots/2025/05/24/230335.json.gz' (HTTP 403)
```

## Issues Fixed So Far
1. ✅ **Environment Variable**: Added missing `GCP_PROJECT` environment variable
2. ✅ **Fork Safety**: Moved `gcsfs.GCSFileSystem` initialization inside the function to avoid concurrency issues
3. ✅ **Date Parsing**: Fixed path parsing logic to correctly extract dates from directory structure (`2025/05/24` format)
4. ✅ **IAM Permissions**: Granted `roles/storage.objectViewer` to the Cloud Function service account (`651058704210-compute@developer.gserviceaccount.com`)

## ✅ SOLUTION IMPLEMENTED

### Root Cause
DuckDB's HTTP client does not inherit the Cloud Function's service account credentials when making direct HTTPS requests to GCS. Unlike `gcsfs` which uses Google's authentication libraries, DuckDB makes unauthenticated HTTP requests when accessing `gs://` URLs.

### Implementation: Hybrid Approach
**Strategy**: Use authenticated `gcsfs` to download files locally → DuckDB processes local files

**Key Changes**:
1. **Download Phase**: Use `gcsfs.open()` to download all required files to a temporary directory
   - Snapshot JSON.gz files from the last 30 days
   - Historical flows parquet file
   - Station capacity CSV file

2. **Processing Phase**: DuckDB reads from local file paths instead of GCS URLs
   - No authentication issues since files are local
   - Same SQL logic and performance benefits

3. **Cleanup**: Automatic cleanup via `tempfile.TemporaryDirectory()` context manager

**Benefits**:
- ✅ Leverages existing service account authentication through `gcsfs`
- ✅ Maintains DuckDB's SQL processing capabilities
- ✅ No changes needed to IAM permissions or environment setup
- ✅ Handles all file types (JSON.gz, Parquet, CSV) consistently

## Current Status
- ✅ Files are accessible via `gsutil` and `gcsfs` 
- ✅ Service account has proper permissions
- ❌ DuckDB's `read_json_auto()` still gets 403 when accessing files via HTTPS

## Hypotheses to Investigate

### 1. **Authentication Method Mismatch**
DuckDB's HTTP client may not inherit the Cloud Function's service account credentials when making direct HTTPS requests to GCS. Unlike `gcsfs` which uses Google's authentication libraries, DuckDB might be making unauthenticated HTTP requests.

### 2. **Missing Authentication Headers**
DuckDB's `read_json_auto()` function may require explicit authentication configuration or headers to access private GCS objects, even with proper IAM permissions.

### 3. **Access Method Inconsistency** 
There may be a difference between:
- How `gcsfs` accesses files (uses Google Cloud Storage API)
- How DuckDB accesses files (direct HTTPS requests)

### 4. **Alternative Implementation Required**
The solution may require downloading files locally first using the authenticated `gcsfs` client, then processing with DuckDB, rather than having DuckDB access GCS directly via URLs.

## Recommended Next Steps
1. Test DuckDB with locally downloaded files to confirm processing logic
2. Investigate DuckDB's GCS authentication configuration options
3. Consider hybrid approach: use `gcsfs` to download → DuckDB to process locally
4. Check if DuckDB supports service account key files or other auth methods
