# WorldInsights - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you set up and run WorldInsights locally.

---

## Prerequisites

- **Python:** 3.11+ (recommended: 3.11.3)
- **pip:** Python package manager
- **Git:** For version control

---

## Step 1: Clone the Repository

```bash
cd /path/to/your/workspace
git clone https://github.com/bonzainsights/WorldInsights.git
cd WorldInsights
git checkout newWI
```

---

## Step 2: Set Up Python Environment

### Option A: Using pyenv (Recommended)
```bash
# Install pyenv if not already installed
# macOS: brew install pyenv
# Linux: curl https://pyenv.run | bash

# Install Python 3.11.3
pyenv install 3.11.3

# Set local Python version
pyenv local 3.11.3

# Verify
python --version  # Should show Python 3.11.3
```

### Option B: System Python
```bash
# Verify Python version (must be 3.11+)
python3 --version

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "Flask|pandas|numpy|duckdb"
```

Expected output:
```
Flask                 3.1.2
pandas                2.3.3
numpy                 2.2.4
duckdb                1.4.3
```

---

## Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
# Or use your preferred editor
```

### Minimum Required Configuration

For **development**, you only need to set:

```env
# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database
DUCKDB_PATH=./data/worldinsights.duckdb

# Cache (use simple for development)
CACHE_TYPE=simple
CACHE_TTL=3600
```

### Optional: API Keys

Most APIs work without keys, but for **NASA** and **NOAA**:

```env
# NASA API (get free key at https://api.nasa.gov/)
NASA_API_KEY=DEMO_KEY  # Works but limited to 10 requests/hour

# NOAA API (get free token at https://www.ncdc.noaa.gov/cdo-web/token)
NOAA_TOKEN=your_token_here
```

### Production Configuration

For **production**, also set:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<strong-random-secret>

# Redis for caching (install: brew install redis or apt install redis)
CACHE_TYPE=redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
REQUIRE_HTTPS=True
RATE_LIMIT_ENABLED=True
```

---

## Step 5: Create Required Directories

```bash
# Create data and logs directories
mkdir -p data data/cache logs
```

---

## Step 6: Run Tests (Optional but Recommended)

```bash
# Run all tests
pytest app/tests/ -v

# Run with coverage
pytest app/tests/ -v --cov=app --cov-report=term-missing

# Run specific test module
pytest app/tests/unit/test_config.py -v
```

Expected output:
```
===================== test session starts ======================
collected XX items

app/tests/unit/test_config.py::test_config_initialization PASSED
app/tests/unit/test_logging.py::test_logging_setup PASSED
...

===================== XX passed in X.XXs ======================
```

---

## Step 7: Start the Application

### Development Server

```bash
# Option 1: Using run.py (recommended for development)
python run.py

# Option 2: Using Flask CLI
export FLASK_APP=run.py
export FLASK_ENV=development
flask run

# Option 3: Direct Python
python -m app.create_app
```

Expected output:
```
2026-03-08 10:00:00 - INFO - WorldInsights application starting in development mode
2026-03-08 10:00:00 - INFO - World Bank API client initialized
2026-03-08 10:00:00 - INFO - WHO API client initialized
2026-03-08 10:00:00 - INFO - FAO API client initialized
2026-03-08 10:00:00 - INFO - NASA API client initialized
2026-03-08 10:00:00 - INFO - WorldInsights application initialized successfully
 * Serving Flask app 'app.create_app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### Production Server (Gunicorn)

```bash
# Install gunicorn (already in requirements.txt)
# Run with gunicorn
gunicorn --config gunicorn_config.py wsgi:app

# Or with custom settings
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

---

## Step 8: Verify Installation

### Test Health Endpoint

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "worldinsights",
  "environment": "development"
}
```

### Test API Endpoints

```bash
# Get available countries
curl http://localhost:5000/api/plot/countries | head -20

# Get available indicators
curl http://localhost:5000/api/plot/indicators | head -20

# Get data for specific indicators
curl "http://localhost:5000/api/plot/data?indicators=NY.GDP.MKTP.CD&countries=USA,CHN&start_year=2020&end_year=2023" | head -30
```

### Test Web Interface

Open your browser and navigate to:
- **Homepage:** http://localhost:5000
- **Dashboard Builder:** http://localhost:5000/dashboard/builder
- **Data Sources:** http://localhost:5000/data-sources
- **3D Globe:** http://localhost:5000/visualization/globe

---

## Step 9: Explore the API

### List All Data Sources

```bash
curl http://localhost:5000/api/data-sources
```

### Get Countries from Specific Source

```bash
# World Bank countries
curl http://localhost:5000/api/data-sources/world_bank/countries

# WHO countries
curl http://localhost:5000/api/data-sources/who/countries
```

### Get Indicators from Specific Source

```bash
# World Bank indicators
curl "http://localhost:5000/api/data-sources/world_bank/indicators?per_page=10"

# WHO indicators by category
curl "http://localhost:5000/api/data-sources/who/indicators?category=mortality"
```

### Smart Filtering

```bash
# Get indicators available for USA
curl "http://localhost:5000/api/availability/indicators?countries=USA"

# Get countries with specific indicator
curl "http://localhost:5000/api/availability/countries?indicators=NY.GDP.MKTP.CD"

# Check availability for combination
curl "http://localhost:5000/api/availability/check?countries=USA,CHN&indicators=NY.GDP.MKTP.CD,SP.POP.TOTL"
```

### Fetch Data

```bash
# Single indicator, single country
curl "http://localhost:5000/api/data?countries=USA&indicators=NY.GDP.MKTP.CD&start_year=2018&end_year=2023"

# Multiple indicators, multiple countries
curl "http://localhost:5000/api/data?countries=USA,CHN,GBR&indicators=NY.GDP.MKTP.CD,SP.POP.TOTL&start_year=2020&end_year=2023"

# All countries for specific indicator
curl "http://localhost:5000/api/data?indicators=SP.POP.TOTL&start_year=2023"
```

---

## Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: SECRET_KEY error

```bash
# Set SECRET_KEY in .env
echo "SECRET_KEY=dev-secret-key" >> .env
```

### Issue: Database errors

```bash
# Create data directory
mkdir -p data

# Check permissions
ls -la data/
```

### Issue: API rate limiting

If you hit rate limits:

```bash
# Enable caching in .env
CACHE_TYPE=simple  # or redis for production
CACHE_TTL=3600

# Use API keys where available
# NASA: Get free key at https://api.nasa.gov/
# NOAA: Get free token at https://www.ncdc.noaa.gov/cdo-web/token
```

### Issue: Port already in use

```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use different port
export PORT=5001
python run.py
```

---

## Next Steps

### 1. Explore the Dashboard Builder

Navigate to `/dashboard/builder` and:
- Select data sources (World Bank, WHO, FAO, NASA)
- Choose indicators (GDP, Population, Health metrics)
- Select countries
- Pick chart types (line, bar, scatter, 3D)
- Save your dashboard

### 2. Try the 3D Globe

Navigate to `/visualization/globe` to see data on an interactive 3D globe.

### 3. Read the Documentation

- **API Documentation:** `docs/apis/README.md`
- **Backend Build Log:** `docs/backend_rebuild_log.md`
- **Architecture:** See project README

### 4. Start Developing

```bash
# Run tests before making changes
pytest app/tests/ -v

# Make your changes
# ...

# Run tests again
pytest app/tests/ -v

# Commit your changes
git add .
git commit -m "feat: your feature description"
```

---

## Development Tips

### Hot Reload

Flask debug mode automatically reloads on code changes:

```bash
# Ensure FLASK_DEBUG=True in .env
python run.py
```

### Debugging

```python
# Add breakpoints with pdb
import pdb; pdb.set_trace()

# Or use Python's built-in breakpoint()
breakpoint()
```

### Logging

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Database Queries

```python
# DuckDB is used for analytics
import duckdb

conn = duckdb.connect('./data/worldinsights.duckdb')
result = conn.execute("SELECT * FROM your_table LIMIT 10").fetchall()
```

---

## Performance Tips

### Enable Redis Caching (Production)

```bash
# Install Redis
# macOS: brew install redis
# Linux: apt install redis-server

# Start Redis
redis-server

# Update .env
CACHE_TYPE=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Pre-fetch Popular Data

```bash
# Create a script to pre-fetch commonly used data
python scripts/prefetch_data.py
```

### Monitor Performance

```bash
# Check API health and latency
curl http://localhost:5000/health/sources
```

---

## Support

### Documentation
- **Quick Start:** This file
- **API Docs:** `docs/apis/README.md`
- **Build Log:** `docs/backend_rebuild_log.md`
- **Main README:** `README.md`

### Common Issues
See the **Troubleshooting** section above.

### Contact
Email: noreply@worldinsights.bonzainsights.com

---

## Verify Your Installation

Run this checklist:

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip list` shows Flask, pandas, etc.)
- [ ] `.env` file created with `SECRET_KEY`
- [ ] Data and logs directories created
- [ ] Tests pass (`pytest app/tests/ -v`)
- [ ] Application starts (`python run.py`)
- [ ] Health endpoint responds (`curl http://localhost:5000/health`)
- [ ] API endpoints work (countries, indicators, data)
- [ ] Web interface loads (http://localhost:5000)

---

**Congratulations!** 🎉 You're ready to explore WorldInsights!

**Last Updated:** 2026-03-08  
**Version:** 2.0.0
