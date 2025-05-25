# Blank Live DPI Error Report

## Current Issue
The `divvy-rollup` Cloud Function executes successfully but generates a **blank/empty DPI file** containing only an empty JSON array `[]`.

**Observed Behavior:**
- ✅ Function deploys and runs without errors
- ✅ Returns HTTP 200: "0 rows → live_dpi.json.gz"
- ❌ Output file contains empty JSON: `[]`
- ❌ No DPI calculations are being generated

## Expected vs Actual Results

**Expected Output Structure:**
```json
[
  {
    "station_id": "123",
    "overflow_per_dock": 0.45,
    "pct_full": 0.78,
    "dpi": 0.351
  },
  ...
]
```

**Actual Output:**
```json
[]
```

## Data Flow Analysis

The function performs these steps:
1. **Snapshot Collection** → Filter last 30 days of snapshots
2. **Percentage Full Calculation** → Calculate `pct_full` per station from snapshots
3. **Historical Data Join** → Join with station flows and capacity data
4. **DPI Calculation** → Compute final dock pressure index

The empty result suggests data is missing at one of these steps.

## Hypotheses to Investigate

### 1. **No Recent Snapshot Data**
**Hypothesis**: There may be no snapshot files in the last 30 days, or snapshots exist but contain no station data.

**Evidence to Check**:
- Are there actually snapshot files from the last 30 days?
- Do the snapshot files contain valid station arrays?
- Is the date filtering logic working correctly with timezone handling?

**Debug Steps**:
```sql
-- Check if snapshots are being loaded
SELECT COUNT(*) FROM snaps;

-- Check if stations exist in snapshots
SELECT COUNT(*) FROM snaps WHERE json_array_length(stations) > 0;
```

### 2. **Station Data Structure Issues**
**Hypothesis**: The UNNEST operation on `stations` array may not be working as expected, or the station objects don't have the expected structure.

**Evidence to Check**:
- What does the actual JSON structure look like in snapshot files?
- Does each station object have `station_id` and `num_docks_available` fields?
- Is the UNNEST operation returning any rows?

**Debug Steps**:
```sql
-- Check what columns are available after UNNEST
SELECT * FROM snaps CROSS JOIN UNNEST(stations) AS unnest LIMIT 5;

-- Check station_id field specifically
SELECT DISTINCT typeof(unnest.station_id) FROM snaps CROSS JOIN UNNEST(stations) AS unnest;
```

### 3. **Historical Data Missing**
**Hypothesis**: The station flows parquet file or station capacity CSV may be missing/empty, causing the final JOIN to return no results.

**Evidence to Check**:
- Does `gs://divvy-live-us-central1/aggregated/station_flows.parquet` exist and contain data?
- Does `gs://divvy-live-us-central1/station_capacity.csv` exist and contain data?
- Are the `station_id` values consistent across all three datasets?

**Debug Steps**:
```sql
-- Check each table individually
SELECT COUNT(*) FROM hist;
SELECT COUNT(*) FROM cap;
SELECT COUNT(*) FROM pct_full;

-- Check for matching station_ids
SELECT COUNT(DISTINCT h.station_id) as hist_stations,
       COUNT(DISTINCT c.station_id) as cap_stations,
       COUNT(DISTINCT pf.station_id) as pct_stations
FROM hist h FULL OUTER JOIN cap c USING(station_id) 
             FULL OUTER JOIN pct_full pf USING(station_id);
```

### 4. **JOIN Logic Issues**
**Hypothesis**: The triple JOIN between `hist`, `cap`, and `pct_full` may be too restrictive, requiring exact matches across all three datasets.

**Evidence to Check**:
- Are there stations in `pct_full` that don't exist in `hist` or `cap`?
- Are there data type mismatches in `station_id` fields?

**Debug Steps**:
```sql
-- Check individual joins
SELECT COUNT(*) FROM hist h JOIN cap c USING(station_id);
SELECT COUNT(*) FROM hist h JOIN pct_full pf USING(station_id);
SELECT COUNT(*) FROM cap c JOIN pct_full pf USING(station_id);
```

### 5. **Timezone/Date Filtering Issues**
**Hypothesis**: The Central Time date filtering may be incorrectly excluding all available snapshot data.

**Evidence to Check**:
- What date range is actually being used for filtering?
- Are snapshot folder dates in UTC vs Central Time causing mismatches?

**Debug Steps**:
- Log the actual date range being used
- Check if removing date filter returns data
- Verify snapshot folder timestamps

## Recommended Next Steps

### Phase 1: Data Availability Check
1. **Verify snapshot data exists**:
   ```bash
   gsutil ls gs://divvy-live-us-central1/snapshots/2025/01/*/
   ```

2. **Check snapshot content structure**:
   ```bash
   gsutil cp gs://divvy-live-us-central1/snapshots/2025/01/27/[latest].json.gz .
   gunzip -c [file].json.gz | jq '.stations[0]'
   ```

### Phase 2: Add Debug Logging
Modify the Cloud Function to include debug output:
```python
print(f"Found {len(filtered_paths)} snapshot files")
print(f"Date range: {since.date()} to {dt.datetime.now(central_tz).date()}")

# After each step
print(f"Loaded {con.sql('SELECT COUNT(*) FROM snaps').fetchone()[0]} snapshots")
print(f"Found {con.sql('SELECT COUNT(*) FROM pct_full').fetchone()[0]} stations with pct_full")
print(f"Loaded {con.sql('SELECT COUNT(*) FROM hist').fetchone()[0]} historical records")
print(f"Loaded {con.sql('SELECT COUNT(*) FROM cap').fetchone()[0]} capacity records")
```

### Phase 3: Progressive Query Testing
Test each part of the data pipeline individually:
1. Load snapshots → verify data exists
2. Calculate pct_full → verify station processing
3. Load historical data → verify files accessible
4. Perform joins → identify where data is lost

### Phase 4: Fallback Strategy
If no recent data exists:
- Expand date range beyond 30 days
- Check if data collection pipeline is working
- Verify snapshot generation is still active

## Priority Investigation Order
1. **Snapshot data availability** (most likely cause)
2. **Historical data files** (required for JOIN)
3. **Date filtering logic** (could exclude valid data)
4. **JSON structure changes** (could break UNNEST)
5. **JOIN key mismatches** (could eliminate all results)

## Success Criteria
Function should generate a non-empty JSON array with DPI calculations for active Divvy bike stations, ranked by dock pressure index. 