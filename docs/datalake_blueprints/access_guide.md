# How to Access Data Lake

This guide explains how to query and inspect data in the Data Lake directly from your terminal or scripts.

## Option 1: The `manage_data.py` CLI (Easiest)

We have built a query tool directly into the manager.

**List all tables/files:**

```bash
python manage_data.py query \
"SELECT * FROM read_parquet('data_lake/*.parquet', union_by_name=True) LIMIT 5"
```

**Query a specific file:**

```bash
python manage_data.py query "SELECT * FROM 'data_lake/weather_2024.parquet' WHERE temperature_2m_mean > 30 LIMIT 10"
```

**Query Country Shapes (GeoJSON):**

```bash
python manage_data.py query "SELECT country, name, source FROM 'data_lake/geo_countries.parquet' LIMIT 5"
```

_(Note: geometry column contains large JSON strings)_

**Check Status:**

```bash
python manage_data.py status
```

_(This prints the `data_lake/README.md` to your terminal)_

## Option 2: DuckDB CLI (Power User)

Since we use standard Parquet files, you can use the standalone `duckdb` binary (if installed) or the python shell.

**Interactive SQL Shell:**

```bash
python3 -c "import duckdb; con=duckdb.connect(); con.execute(\"SELECT * FROM 'data_lake/*.parquet'\").show()"
```

**One-liner Query:**

```bash
duckdb -c "SELECT * FROM 'data_lake/weather_2024.parquet' LIMIT 5"
```

_(Requires `brew install duckdb` on Mac)_

## Option 3: Python Script

Use this snippet in your own analysis scripts (Jupyter notebooks, etc).

```python
import duckdb
import pandas as pd

# Connect (In-Memory is fine for reading parquet)
con = duckdb.connect()

# Load all weather data
df = con.query("SELECT * FROM 'data_lake/weather_*.parquet'").to_df()

print(df.head())
```

## Troubleshooting

- **"File not found"**: Ensure you are in the project root (`/path/to/WorldInsights`).
- **S3 Access**: If `DATA_STORAGE_TYPE=s3` in `.env`, these local commands wont work directly on files. usage `manage_data.py query` which handles the S3 connection for you!
