# Divvy Live: Dock Pressure Index Dashboard

A live dashboard that answers the question: **Which Divvy bike station needs more racks?** by calculating a Dock Pressure Index (DPI) from historical trip data and real-time capacity monitoring.

## Project Overview

### Problem Statement
How can we determine which Divvy bike station would benefit from another rack?

### Thesis
There exists a Divvy bike station in Chicago that would benefit from at least one more rack because it would solve user pain or increase Divvy's profits.

### Benefits We Track
1. **Customer pain**: Reduce difficulty in finding a rack
2. **Divvy profits**: Reduce operational expenses in having to rebalance docks

## Success Metrics

| Stakeholder | Proxy metric you can actually calculate | Why it works |
|-------------|----------------------------------------|--------------|
| **Riders** | % of time a station is *effectively full* (all docks occupied) | Captures "I can't dock" pain exactly |
| **Divvy** | Net bike **accumulation** at a station (ends − starts) expressed *per dock* | If a station regularly absorbs more bikes than it releases, operations spends money re-balancing or loses revenue when riders give up |

## Dock Pressure Index (DPI)

Our solution provides a numerical score that combines both metrics:

```
DPI = (Ends − Starts) / Dock_Count × %Time_Full
    = "overflow per dock" × "percent time full"
```

**Higher DPI ⇒ stronger case for more racks**

- **Net accumulation per dock**: Tells you structural imbalance (the station soaks up more bikes than it sends out)
- **% time full**: Tells you *operational pain* (how often riders actually hit a full dock)

### Understanding the Patterns

| Pattern | What it means operationally | Example fix |
|---------|----------------------------|-------------|
| **High overflow + High %-full** | Station *attracts* far more bikes than it releases **and** riders frequently hit a wall | *Add docks* **and** increase re-balancing |
| **Low overflow + High %-full** | Station *fills quickly* but also *drains quickly* (e.g., morning crush-in, evening flush-out). Capacity isn't the root cause; the tempo is | **More frequent re-balancing** or dynamic pricing, not necessarily extra docks |
| **High overflow + Low %-full** | Bikes pile up but riders rarely hit "no dock" because ops clear it out just in time | *Maybe* bigger station, *maybe* keep the van visits |
| **Low overflow + Low %-full** | Not much action either way: dock doesn't fill up or experience fullness much | Fine! |

### Dashboard Visualization Strategy

| Axis 1 | Axis 2 | Dashboard Interpretation |
|--------|--------|-------------------------|
| Overflow per dock | % time full | Scatter plot → top-right = "needs racks", top-left = "needs vans", bottom-right = "needs usage-boost", bottom-left = fine |

## Known Limitations

### Main Critiques to Our Approach

1. **User pain metric (% full) is not weighted by traffic times**
   - A dock could be 100% full during off hours only, but that doesn't matter because fewer people want to dock then
   - The data only measures 'successful' docks, not 'attempted' or 'diverted' trips

2. **Business metric focuses only on operational cost reduction**
   - Doesn't consider ways to increase revenue
   - Divvy likely already tracks and optimizes rebalancing costs

## Technical Solution

### Data Pipeline Architecture

| Cloud Function | Reads | Writes | Purpose |
|----------------|-------|--------|---------|
| **scraper (15 min)** | GBFS `station_status.json` | #1 snapshots | Raw feed → bucket; no calculations |
| **rollup (daily)** | #1 snapshots + #2 capacity + #3 flows | #4 live_dpi | Calculates `% time full`, `overflow_per_dock`, `dpi` |
| **read-api (on demand)** | #4 live_dpi.json.gz | — | Returns JSON to the Next.js dashboard |

### Divvy Data Sources

| # | Dataset (⇢ Bucket path) | Original source & endpoint | Who grabs it | Fields you actually use | How it feeds the DPI metric |
|---|-------------------------|---------------------------|--------------|------------------------|----------------------------|
| **1** | **Real-time station status snapshots**<br>`gs://divvy-live-REG/snapshots/YYYY/MM/DD/HHMMSS.json.gz` | **GBFS** feed:<br>`https://gbfs.divvybikes.com/gbfs/en/station_status.json` | **scraper Cloud Function**<br>(runs every 15 min) | `station_id`<br>`num_docks_available`<br>`is_returning` | 1. For each snapshot, `is_full = num_docks_available == 0 AND is_returning`<br>2. Daily roll-up averages `is_full` ⇒ **% time full** |
| **2** | **Station metadata / capacity**<br>`gs://divvy-live-REG/station_capacity.csv` | Either of two interchangeable sources:<br>• GBFS `station_information.json` (*capacity field*)<br>• Chicago Data Portal "Divvy Bicycle Stations" CSV | **one-off manual download** (or tiny helper script) | `station_id`<br>`capacity` (dock count)<br>`lat`, `lon`, `name` | *Divisor* in `overflow_per_dock = (ends − starts) / capacity` |
| **3** | **Historical trip flows**<br>`gs://divvy-live-REG/aggregated/station_flows.parquet` | Chicago Data Portal monthly files:<br>`Divvy_Trips_2024_MM.csv` (…2023, 2022) | **local DuckDB notebook** (run once) | `start_station_id`, `end_station_id` → aggregated to:<br>`starts`, `ends` per station | 1. Computes **net overflow** `(ends − starts)`<br>2. Roll-up divides by capacity ⇒ overflow / dock |
| **4** | **Live DPI table**<br>`gs://divvy-live-REG/aggregated/live_dpi.json.gz` | Produced—not sourced—by your roll-up function | **rollup Cloud Function** (daily) | `station_id`, `overflow_per_dock`, `pct_full`, `dpi` (product) | Exposed to dashboard via read-API; drives "top-stations" table & map |

### Quick Reference: Data Artifacts

| Artifact in bucket | Built from | Grabbed by | Used for |
|--------------------|------------|------------|----------|
| `snapshots/YYYY/...` | GBFS `station_status.json` | **scraper Fn** (15 min) | % Time Full |
| `station_capacity.csv` | GBFS `station_information.json` | one-off helper script (opt: monthly, manual) | capacity divisor |
| `aggregated/station_flows.parquet` | Monthly trip CSVs from `divvy-tripdata.s3.amazonaws.com` | local DuckDB job (opt: monthly, manual) | net overflow |
| `aggregated/live_dpi.json.gz` | roll-up Fn (daily) combining the three above | — | dashboard feed |

### Why Each Dataset is Essential to DPI

- **% time full** ← only real-time snapshots (#1) tell you how often riders hit a full dock
- **Overflow per dock** ← only historical trips (#3) reveal net bike accumulation; dividing by **capacity** (#2) normalizes big vs. small stations
- **DPI** = overflow_per_dock × % time full → saved daily (#4) so the website can stay blazing-fast and free of heavy SQL

## Repository Structure

```
divvy-live/                      ← Monorepo for data pipeline + website
│
├─ .gitignore                    ← Comprehensive gitignore for Python/Node.js
├─ vercel.json                   ← Vercel config for deploying website-reporting/ subfolder
├─ README.md
│
├─ commands-setup/               ← Setup scripts and commands
│
├─ debugging-prompts/            ← Reports to facilitate development
│
├─ gcp-functions/
│   ├─ scraper/                  ← 20-min snapshot (write path)
│   │   ├─ main.py
│   │   └─ requirements.txt
│   │
│   ├─ rollup/                   ← daily DPI calculator (write path)
│   │   ├─ main.py
│   │   └─ requirements.txt
│   │
│   └─ api/                      ← lightweight read-API (JSON)
│       ├─ main.py
│       └─ requirements.txt
│
├─ data-prep/                    ← Scripts & one-off jobs to prepare historical/static data
│   ├─ historical_trip_data_csvs/  ← Raw historical trip CSVs (downloaded)
│   ├─ download_historical_trips.sh ← Downloads last 12 months of trip data
│   ├─ process_trips.py             ← Aggregates trips to station_flows.parquet using DuckDB
│   ├─ get_station_capacity.py      ← Fetches station metadata to station_capacity.csv
│   ├─ station_flows.parquet        ← Output: Aggregated trips (uploaded to GCS)
│   ├─ station_capacity.csv         ← Output: Station capacity/metadata (uploaded to GCS)
│   ├─ flows.duckdb                 ← DuckDB database file for processing
│   └─ export-and-upload.sh         ← (Optional) Helper for GCS uploads
│
└─ website-reporting/            ← Next.js 15+ app (TypeScript, Tailwind, shadcn/ui) → Vercel
    ├─ src/
    │   ├─ app/
    │   │   ├─ api/dpi/route.ts     ← calls GCP read-API
    │   │   ├─ (report)/page.tsx    ← dashboard report page
    │   │   ├─ layout.tsx
    │   │   ├─ page.tsx
    │   │   └─ globals.css
    │   ├─ components/ui/           ← shadcn components (button, card, table, badge)
    │   └─ lib/utils.ts
    ├─ package.json
    ├─ tailwind.config.ts
    ├─ components.json              ← shadcn config
    └─ next.config.ts
```

## System Specifications

- **Live % full data updates**: Every 20 minutes
- **Rollup aggregation**: Daily at 2:15 AM
- **Historical trip data**: Last 12 months from May 24, 2025
- **Optimization**: Calculates daily % full numbers to save memory/money on DuckDB calculations

## Implementation Progress

### Technical Implementation Steps

1. ~~Google Cloud prereqs setup & repo setup~~
2. ~~Create storage bucket~~
3. ~~Build station_flows.parquet locally using historical data with DuckDB~~
    1. ~~Run script: Grab the last 12 months of trip CSVs from AWS~~
    2. ~~Run python script: Compute starts / ends per station using local DuckDB~~
    3. ~~Export & upload to Google Cloud~~
    4. *~~Caveat: This is done once and best to be updated over time (can manually update later)~~*
4. ~~Create a tiny helper script to get the capacity field (and station metadata) from GBFS station_information.json~~
    1. ~~Run the script~~
    2. *~~Caveat: This could also change — could update at same time as updating station_flows.parquet file~~*
5. ~~Setup Google Cloud Functions for live data~~
    1. ~~Deploy scraper~~
    2. ~~Deploy rollup~~
    3. Deploy API
6. ~~Schedule with Cloud Scheduler~~
    1. ~~divvy-rollup-daily~~
    2. ~~divvy-scraper-15~~
7. ~~Setup Next.js website inside /website-reporting~~
    1. ~~Configure divvy-live project to support a Next.js website inside the /website-reporting folder (deployed to Vercel)~~
    2. ~~app/api/dpi/route.ts: Create function to call the api/main.py GCF function to read live_dpi.parquet~~
    3. app/(report)/page.tsx: Create page to display a dashboard-like report of the stations ranked DESC by DPI
8. Post blog with first dashboard report!
9. **FUTURE**: Setup live map

## Next Steps

- Finish dashboard report page
- Analyze initial results and validate DPI effectiveness
- Consider implementing time-weighted fullness metrics
- Explore revenue optimization opportunities