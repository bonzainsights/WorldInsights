# Data pipeline Structure & Maintenance

This document explains **where** things are and **how** to modify the Data Lake pipeline.

## 1. Directory Structure

```text
WorldInsights/
├── .env                        <-- Config (Keys, Intervals, Storage Type)
├── manage_data.py              <-- The Orchestrator (CLI)
├── data_lake/                  <-- STORAGE (Local parquet files)
│   ├── README.md               <-- Auto-generated Status Report
│   ├── indicators.yaml         <-- [NEW] Central Config for Data Points
│   └── *.parquet               <-- The Data (e.g., weather_2024.parquet, geo_countries.parquet)
└── app/
    ├── core/
    │   └── data_config.py      <-- Config Logic (Loads .env)
    └── services/
        ├── data_lake_service.py <-- Storage Adapter (S3 vs Local I/O)
        └── data_ingestion/      <-- INGESTORS (The Logic)
            ├── base.py          <-- Logic to load indicators.yaml
            ├── geo.py           <-- [NEW] 3D Globe Shapes
            ├── weather.py       <-- Weather Ingestor
            ├── worldbank.py     <-- WB Ingestor
            └── ...
```

## 2. How it Works (The Flow)

1.  **Trigger**: User runs `python manage_data.py update` (or scheduler runs it).
2.  **Config**: `DataConfig` loads intervals from `.env`.
3.  **Check**: `DataManager` asks each Ingestor: _"Should you update?"_
    - Ingestor checks `data_lake/` for its specific file.
    - Compares file modification time vs `INTERVAL_HOURS`.
4.  **Ingest**: If YES, Ingestor calls API -> Cleans Data -> Returns List[Dict].
5.  **Save**: `DataLakeService` writes List[Dict] to `.parquet`.
6.  **Report**: `DataManager` updates `data_lake/README.md`.

## 3. Maintenance Guide

### How to Add New Indicators?

1.  **Open `data_lake/indicators.yaml`**.
2.  Add lines under the relevant source:
    ```yaml
    worldbank:
      indicators:
        - code: "NY.GDP.PCAP.CD"
          name: "GDP Per Capita"
        - code: "New.Code.Here"
          name: "My New Indicator"
    ```
3.  Run `python manage_data.py update --source WorldBank`.
4.  Done! No code changes needed.

### How to Add a New Data Source?

1.  **Create Ingestor**: Add `app/services/data_ingestion/my_new_source.py`.
    ```python
    class MySourceIngestor(BaseIngestor):
        @property
        def name(self): return "MySource"
        @property
        def interval_hours(self): return 24
        def ingest(self): ... return data
    ```
2.  **Register**: Import and add to `self.ingestors` list in `manage_data.py`.
3.  **Config (Optional)**: Add `DATA_MYSOURCE_UPDATE_INTERVAL` to `.env` and `data_config.py` if you want it configurable.

### How to Change Update Schedule?

- **Do not edit code.**
- Edit `.env`: `DATA_WEATHER_UPDATE_INTERVAL=12` (Change from 6h to 12h).
- Run `python manage_data.py check` to verify.

### How to Switch to S3?

1.  Create AWS S3 Bucket.
2.  Edit `.env`:
    ```bash
    DATA_STORAGE_TYPE=s3
    DATA_LAKE_PATH=s3://my-bucket-name
    AWS_ACCESS_KEY_ID=...
    AWS_SECRET_ACCESS_KEY=...
    AWS_REGION=us-east-1
    ```
3.  Run `python manage_data.py check` (It will now check S3 objects).
