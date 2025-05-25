import duckdb
import glob
import os

# Define the directory containing the CSV files
csv_directory = "data-prep/historical_trip_data_csvs/"
output_parquet_file = "data-prep/station_flows.parquet"
duckdb_file = "data-prep/flows.duckdb"

# Find all CSV files in the directory
csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))

if not csv_files:
    print(f"No CSV files found in {csv_directory}")
else:
    # Connect to DuckDB. This will create a new database file if it doesn't exist.
    con = duckdb.connect(database=duckdb_file, read_only=False)

    # Create a table from the CSV files
    # DuckDB can directly read from a list of CSVs and handle schema detection.
    # It's important to ensure all CSVs have consistent column names for 'start_station_id' and 'end_station_id'.
    # The README mentions 'start_station_id' and 'end_station_id' are the fields you actually use.
    # We'll assume these are the correct column names in your CSVs.
    # If your CSVs have different date/time formats, you might need to specify parsing options.
    # For simplicity, we'll assume DuckDB's auto-detection works.
    print(f"Reading CSV files from {csv_directory} into DuckDB table 'trips'...")
    con.execute(f"CREATE OR REPLACE TABLE trips AS SELECT start_station_id, end_station_id FROM read_csv_auto({csv_files}, union_by_name=true)")

    # Aggregate data to get starts and ends per station
    # Starts: count of trips originating from each station
    # Ends: count of trips ending at each station
    print("Aggregating trip data...")
    query = """
    CREATE OR REPLACE TABLE station_flows AS
    WITH starts AS (
        SELECT
            start_station_id AS station_id,
            COUNT(*) AS num_starts
        FROM trips
        WHERE start_station_id IS NOT NULL
        GROUP BY start_station_id
    ),
    ends AS (
        SELECT
            end_station_id AS station_id,
            COUNT(*) AS num_ends
        FROM trips
        WHERE end_station_id IS NOT NULL
        GROUP BY end_station_id
    )
    SELECT
        COALESCE(s.station_id, e.station_id) AS station_id,
        COALESCE(s.num_starts, 0) AS starts,
        COALESCE(e.num_ends, 0) AS ends
    FROM starts s
    FULL OUTER JOIN ends e ON s.station_id = e.station_id;
    """
    con.execute(query)

    print(f"Aggregation complete. Results are in the 'station_flows' table in {duckdb_file}")

    # The export to Parquet is handled by export-and-upload.sh, so we don't do it here.
    # If you wanted to do it in Python:
    # con.execute(f"COPY station_flows TO '{output_parquet_file}' (FORMAT PARQUET);")
    # print(f"Exported station_flows to {output_parquet_file}")

    # Close the connection
    con.close()
    print("Process complete.") 