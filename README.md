Project overview: this project is creating a "live" dashboard that answers the question: which divvy bike station needs more racks? by calculating a metric DPI from historical trip data and live capacity numbers


Divvy Data Used Recap

| #     | Dataset (⇢ Bucket path)                                                                               | Original source & endpoint                                                                                                                             | Who grabs it                                        | Fields you actually use                                                                | How it feeds the DPI metric                                                                                                            |
| ----- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **Real-time station status snapshots**  <br>`gs://divvy-live-REG/snapshots/YYYY/MM/DD/HHMMSS.json.gz` | **GBFS** feed: <br>`https://gbfs.divvybikes.com/gbfs/en/station_status.json`                                                                           | **scraper Cloud Function** <br>(runs every 15 min)  | `station_id`  <br>`num_docks_available`  <br>`is_returning`                            | 1. For each snapshot, `is_full = num_docks_available == 0 AND is_returning`. <br>2. Daily roll-up averages `is_full` ⇒ **% time full** |
| **2** | **Station metadata / capacity**  <br>`gs://divvy-live-REG/station_capacity.csv`                       | Either of two interchangeable sources: <br>• GBFS `station_information.json` (*capacity field*) <br>• Chicago Data Portal "Divvy Bicycle Stations" CSV | **one-off manual download** (or tiny helper script) | `station_id`  <br>`capacity` (dock count)  <br>`lat`, `lon`, `name`                    | *Divisor* in `overflow_per_dock = (ends − starts) / capacity`                                                                          |
| **3** | **Historical trip flows**  <br>`gs://divvy-live-REG/aggregated/station_flows.parquet`                 | Chicago Data Portal monthly files: <br>`Divvy_Trips_2024_MM.csv` (…2023, 2022)                                                                         | **local DuckDB notebook** (run once)                | `start_station_id`, `end_station_id` → aggregated to: <br>`starts`, `ends` per station | 1. Computes **net overflow** `(ends − starts)` <br>2. Roll-up divides by capacity ⇒ overflow / dock                                    |
| **4** | **Live DPI table**  <br>`gs://divvy-live-REG/aggregated/live_dpi.json.gz`                             | Produced—not sourced—by your roll-up function                                                                                                          | **rollup Cloud Function** (daily)                   | `station_id`, `overflow_per_dock`, `pct_full`, `dpi` (product)                         | Exposed to dashboard via read-API; drives "top-stations" table & map                                                                   |


Quick reference table of required Divvy data

| Artifact in bucket                 | Built from                                               | Grabbed by                      | Used for         |
| ---------------------------------- | -------------------------------------------------------- | ------------------------------- | ---------------- |
| `snapshots/YYYY/...`               | GBFS `station_status.json`                               | **scraper Fn** (15 min)         | % Time Full      |
| `station_capacity.csv`             | GBFS `station_information.json`                          | one-off helper script (monthly) | capacity divisor |
| `aggregated/station_flows.parquet` | Monthly trip CSVs from `divvy-tripdata.s3.amazonaws.com` | local DuckDB job (once)         | net overflow     |
| `aggregated/live_dpi.json.gz`      | roll-up Fn (daily) combining the three above             | —                               | dashboard feed   |





Repo Layout

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
│   ├─ scraper/                  ← 15-min snapshot (write path)
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




- live % full data updates every 15 min
- rollup aggregation of data happens every day (2:15AM)
- historical trip data used in overflow calculation is last 12 months from MAy 24 2025




Technical Implementation steps:

1. ~~google cloud prereqs setup & repo setup~~
2. ~~create storage bucket~~
3. ~~Build station_flows.parquet locally using historical data with DuckDB~~
    1. ~~run script: Grab the last 12 months of trip CSVs from AWS~~
    2. ~~run python script: Compute starts / ends per station using local duckdb~~
    3. ~~Export & upload to google cloud~~
    4. *~~caveat: this is done once and best to be updated overtime (i can manually update later)~~*
4. ~~Create a tiny helper script to get the capacity field (and station metadata) from GBFS station_information.json~~
    1. ~~run the script~~
    2. *~~caveat: this could also change — could update at same time as updating station_flows.parquet file~~*
5. ~~setup google cloud functions for live data~~
    1. ~~deploy scraper~~
    2. ~~deploy rollup~~
    3. deploy api
6. ~~schedule with cloud scheduler~~
    1. ~~divvy-rollup-daily~~
    2. ~~divvy-scrapper-15~~
7. ~~setup nextjs website inside /website-reporting~~
    1. ~~configure divvy-live project to support a nextjs website inside the /website-reporting folder (deployed to vercel)~~
    2. app/api/dpi/route.ts: create function to call the api/main.py gcf function to read live_dpi.parquet
    3. app/(report)/page.tsx: create page to display a dashboard-like report of the stations ranked DESC by DPI
8. post blog with first dashboard report!
9. FUTURE: setup live map