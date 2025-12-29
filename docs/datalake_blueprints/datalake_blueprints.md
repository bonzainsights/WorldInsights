# WorldInsights Data Lake Blueprints

## 1. Architecture & Location Strategy

### The Decision: Where to store the data?

You asked about the safest/best location. Here is the tiered strategy:

#### **Phase 1: Local Development (The "Root" Approach)**

- **Location:** `/data_lake` directory in the project root.
- **Why:** Zero cost, millisecond latency, no internet required for development.
- **Safety:** We add `data_lake/` to `.gitignore` so you don't accidentally push 2GB of data to GitHub.

#### **Phase 2: Production (The "Safe" Way)**

- **Problem:** If you deploy to a cloud container (Heroku, AWS ECS, DigitalOcean App Platform), the file system is _ephemeral_. If the app restarts, the `/data_lake` folder in the root is wiped.
- **Solution A (Mounted Volume):** If using a VPS or Docker, we mount a strict persistent volume to `/data_lake`.
- **Solution B (Object Storage - Recommended):** We move the files to **AWS S3** or **Google Cloud Storage**.
  - **DuckDB Magic:** DuckDB can read Parquet files directly from S3 (`s3://bucket/weather.parquet`) as if they were local files.
  - **Abstraction:** Our code will use a variable `DATA_LAKE_PATH`.
    - Dev: `DATA_LAKE_PATH = "./data_lake"`
    - Prod: `DATA_LAKE_PATH = "s3://my-wi-bucket"`

**Verdict:** We build for **Local Root** now, but write the code using `fsspec` style paths so switching to S3 later is just a config change, not a code rewrite.

---

## 2. Pipeline Design

The system acts as a "Data Pump" that moves data from APIs -> Parquet Files.

### Core Components

1.  **`DataConfig`**: The Brain. detailed configuration of _when_ to update each source (e.g., Weather=6h, WB=30d). Loaded from `.env`.
2.  **`DataManager` (Orchestrator)**: The Boss. Check schedules, launches ingestors, updates logs.
3.  **`Ingestors` (Workers)**: Specialized modules for each API.
    - _Input_: Raw API Data (JSON).
    - _Process_: Clean, Normalize, Type-Cast.
    - _Output_: Parquet File (Partitioned by Year).

### The "Tiered" Update Schedule

| Tier          | Update Freq     | Sources                           | Strategy                                      |
| :------------ | :-------------- | :-------------------------------- | :-------------------------------------------- |
| **Fast Lane** | Every 3-6 Hours | Weather (OpenMeteo), Stocks, News | Append-only or Daily Partition overwrites.    |
| **Slow Lane** | Monthly/Weekly  | World Bank, WHO, FAO              | Full Year overwrite (datasets change rarely). |
| **Static**    | yearly/Manual   | NASA Historical, Geo Shapes       | Download once, keep forever.                  |

---

## 3. Data Structure (Schema)

We will use **Parquet** (Columnar Storage). It compress 1GB of JSON to ~100MB and is queryable via SQL.

### Directory Layout

```text
data_lake/
├── README.md               <-- Auto-generated status report
├── weather/                <-- Partitioned by Year
│   ├── weather_2023.parquet
│   ├── weather_2024.parquet
│   └── weather_2025.parquet
├── worldbank/
│   ├── gdp_history.parquet
│   └── population.parquet
└── metadata/
    └── ingestion_log.json  <-- Audit trail of when things ran
```

### Universal Schema

To make cross-correlation easy (e.g., "Show me GDP vs Rainfall"), all tables generally follow this "Long Format" shape where possible:

| Country (ISO3) | Date (YYYY-MM-DD) | Indicator (String) | Value (Float) | Source    |
| :------------- | :---------------- | :----------------- | :------------ | :-------- |
| USA            | 2024-01-01        | temp_mean          | 12.5          | OpenMeteo |
| USA            | 2024-01-01        | gdp_usd            | 25T           | WorldBank |

---

## 4. Security & Quality

### Security

- **API Keys:** Never stored in code. Always in `.env`.
- **Git:** `.gitignore` ensures data never leaks to repo.
- **Access:** In extraction logic, we sanitize inputs to prevent "SQL Injection" style attacks if we were constructing dynamic queries strings (though DuckDB is safer).

### Light-Weight Checks (Quality Control)

Before saving a Parquet file, the Ingestor runs these sanity checks:

1.  **Row Count:** Did we fetch 0 rows? (Alarm!)
2.  **Null Check:** Is the `value` column 100% null? (Alarm!)
3.  **Freshness:** Is the data actually new? (Prevents redundant IO).

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Day 1)

1.  Setup `DataConfig` & `.env`.
2.  Create `BaseIngestor` class.
3.  Implement `WeatherIngestor` (Proof of Concept).
4.  Implement `DataManager` CLI.

### Phase 2: Expansion (Day 2)

1.  Implement `WorldBankIngestor` & `WHOIngestor`.
2.  Add `metadata/ingestion_log.json` logic.

### Phase 3: Production Prep (Future)

1.  Add S3 support for `DATA_LAKE_PATH`.
2.  Create a Docker Volume mount for the data lake.
