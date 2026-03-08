# WorldInsights - Connected Data APIs

## Overview

WorldInsights integrates with **12+ free, open data APIs** providing access to **20,000+ indicators** across **266 countries** with data ranging from **1960 to present**.

All APIs are:
- ✅ **Free** - No cost for access
- ✅ **Open** - Publicly available
- ✅ **Authoritative** - Official sources (UN agencies, governments)
- ✅ **Reliable** - Production-ready with SLAs
- ✅ **Well-documented** - Comprehensive API docs

---

## Primary API Integrations

### 1. World Bank Open Data API 🏦

**Status:** ✅ Fully Implemented  
**Indicators:** 16,000+  
**Countries:** 266  
**Data Range:** 1960-2023  
**Authentication:** None required  

#### Configuration
```env
WORLD_BANK_BASE_URL=https://api.worldbank.org/v2
WORLD_BANK_ENABLED=True
WORLD_BANK_RATE_LIMIT=10 per second
WORLD_BANK_CACHE_TTL=86400
```

#### Key Endpoints
- `/country` - List all countries
- `/indicator` - List all indicators  
- `/country/{code}/indicator/{code}` - Fetch time-series data
- `/topic/{id}/indicator` - Indicators by topic

#### Categories
| Category | Indicators | Examples |
|----------|------------|----------|
| Economy | 2,500+ | GDP, Inflation, Trade |
| Population | 500+ | Population, Birth rate, Migration |
| Health | 1,000+ | Mortality, Diseases, Nutrition |
| Education | 300+ | Enrollment, Literacy, Spending |
| Environment | 400+ | CO2 emissions, Energy, Pollution |
| Poverty | 200+ | Income inequality, Gini index |
| Trade | 600+ | Imports, Exports, Tariffs |

#### Usage Example
```python
from app.infrastructure.api_clients.world_bank import WorldBankClient

client = WorldBankClient()

# Get countries
countries, error = client.get_countries()

# Get indicators
indicators, error = client.get_indicators(category='economy')

# Get data
data, error = client.get_data(
    country_code='USA',
    indicator_code='NY.GDP.MKTP.CD',  # GDP
    start_year=2018,
    end_year=2023
)
```

#### Popular Indicators
```
NY.GDP.MKTP.CD          - GDP (current US$)
NY.GDP.PCAP.CD          - GDP per capita (current US$)
NY.GDP.MKTP.KD.ZG       - GDP growth (annual %)
SP.POP.TOTL             - Population, total
SP.DYN.CBRT.IN          - Birth rate (per 1,000)
SH.DYN.MORT             - Mortality rate, under-5
SE.PRM.NENR             - School enrollment, primary (%)
EN.ATM.CO2E.PC          - CO2 emissions (metric tons per capita)
SI.POV.DDAY             - Poverty headcount ratio at $2.15/day
NE.EXP.GNFS.CD          - Exports of goods and services (US$)
```

#### Documentation
https://datahelpdesk.worldbank.org/knowledgebase/api

---

### 2. WHO Global Health Observatory 🏥

**Status:** ✅ Fully Implemented  
**Indicators:** 1,000+  
**Countries:** 194 (WHO member states)  
**Data Range:** 2000-2023  
**Authentication:** None required  

#### Configuration
```env
WHO_BASE_URL=https://ghoapi.azureedge.net/api
WHO_ENABLED=True
WHO_RATE_LIMIT=5 per second
WHO_CACHE_TTL=86400
```

#### Key Endpoints
- `/COUNTRY` - List countries
- `/INDICATOR` - List indicators
- `/{indicator_code}` - Fetch data with filter

#### Categories
| Category | Indicators | Examples |
|----------|------------|----------|
| Mortality | 50+ | Death rate, Life expectancy |
| Diseases | 100+ | Malaria, TB, HIV, Hepatitis |
| Vaccination | 30+ | DTP3, Measles, BCG |
| Nutrition | 40+ | Undernourishment, Stunting |
| Maternal Health | 30+ | Maternal mortality, Antenatal care |
| Infectious Diseases | 80+ | Malaria, TB, HIV prevalence |
| Noncommunicable Diseases | 60+ | Blood pressure, Diabetes, Obesity |

#### Usage Example
```python
from app.infrastructure.api_clients.who import WHOClient

client = WHOClient()

# Get health indicators
indicators, error = client.get_indicators(category='mortality')

# Get data for specific indicator
data, error = client.get_data(
    country_code='USA',
    indicator_code='WHOSIS_000001',  # Crude death rate
    start_year=2018,
    end_year=2023
)
```

#### Popular Indicators
```
WHOSIS_000001           - Crude death rate (per 1000)
WHOSIS_000004           - Life expectancy at birth (years)
SDG_MORT_NMR            - Neonatal mortality rate (per 1000)
SDG_MORT_U5MR           - Under-5 mortality rate (per 1000)
IMDTC                   - Immunization DTP3 coverage (%)
GHO_NUT_000001          - Prevalence of undernourishment (%)
MATERNAL_MORTALITY_RATIO - Maternal mortality ratio
NCD_RIS_11              - Obesity prevalence (%)
TOB_PREV                - Tobacco use prevalence (%)
```

#### Documentation
https://www.who.int/data/gho/data/gho-api

---

### 3. FAO FAOSTAT API 🌾

**Status:** ✅ Fully Implemented  
**Indicators:** 3,000+  
**Countries:** 200+  
**Data Range:** 1961-2023  
**Authentication:** None required  

#### Configuration
```env
FAO_BASE_URL=https://www.fao.org/faostat/api/v2
FAO_ENABLED=True
FAO_RATE_LIMIT=5 per second
FAO_CACHE_TTL=86400
```

#### Key Endpoints
- `/codes/countries` - List countries
- `/codes/elements` - List indicators
- `/codes/items` - List crops/products
- `/data` - Fetch data (POST request)

#### Categories
| Category | Indicators | Examples |
|----------|------------|----------|
| Production | 500+ | Crops, Livestock, Forestry |
| Trade | 400+ | Imports, Exports by commodity |
| Food Security | 100+ | Food balance sheets, Calories |
| Land Use | 50+ | Agricultural area, Irrigation |
| Inputs | 80+ | Fertilizers, Pesticides, Machinery |
| Emissions | 40+ | GHG emissions from agriculture |

#### Usage Example
```python
from app.infrastructure.api_clients.fao import FAOClient

client = FAOClient()

# Get production data for wheat
data, error = client.get_production_data(
    country_iso3='USA',
    item_codes=['15'],  # Wheat
    start_year=2018,
    end_year=2023
)

# Get trade data
data, error = client.get_trade_data(
    country_iso3='CHN',
    item_codes=['27'],  # Rice
    start_year=2020,
    end_year=2023
)
```

#### Popular Indicators
```
5510                    - Production quantity (tonnes)
5312                    - Yield (hg/ha)
5218                    - Area harvested (ha)
5910                    - Import quantity (tonnes)
5912                    - Export quantity (tonnes)
661                     - Food supply quantity (kg/capita/year)
664                     - Food supply calories (kcal/capita/day)
5101                    - Agricultural area (ha)
5105                    - Arable land (ha)
```

#### Key Items (Crops/Products)
```
15                      - Wheat
27                      - Rice
56                      - Maize
236                     - Soybeans
48                      - Potatoes
1005                    - Meat (total)
1076                    - Milk
10000                   - Fish
```

#### Documentation
https://www.fao.org/faostat/en/#home

---

### 4. NASA/NOAA Climate Data API 🛰️

**Status:** ✅ Fully Implemented  
**Indicators:** Climate & Earth Science  
**Countries:** Global coverage  
**Data Range:** Varies by dataset  
**Authentication:** API key (free)  

#### Configuration
```env
NASA_BASE_URL=https://api.nasa.gov
NASA_CDO_BASE_URL=https://www.ncdc.noaa.gov/cdo-web/api/v2
NASA_API_KEY=DEMO_KEY
NASA_ENABLED=True
NASA_RATE_LIMIT=10 per hour
NASA_CACHE_TTL=604800
```

#### Key Endpoints (NASA)
- `/planetary/earth/climate` - Climate indicators
- `/planetary/earth/imagery` - Earth imagery
- `/neo/rest/v1/feed` - Near Earth Objects
- `/planetary/apod` - Astronomy Picture of Day

#### Key Endpoints (NOAA)
- `/data` - Climate observations
- `/stations` - Weather stations
- `/datasets` - Available datasets
- `/datatypes` - Data types

#### Categories
| Category | Data Types | Examples |
|----------|------------|----------|
| Climate | 10+ | Temperature, Precipitation |
| Earth Imagery | Global | Satellite imagery |
| Natural Hazards | Various | Storms, Floods, Fires |
| Space Weather | Solar | Solar flares, Geomagnetic |

#### Usage Example
```python
from app.infrastructure.api_clients.nasa import NASAClient, NOAAClient

# NASA Client
nasa_client = NASAClient(api_key='YOUR_KEY')

# Get Earth imagery
imagery, error = nasa_client.get_earth_imagery(
    lat=40.7128,
    lon=-74.0060,
    date='2023-06-15'
)

# NOAA Client
noaa_client = NOAAClient(token='YOUR_TOKEN')

# Get climate data
data, error = noaa_client.get_data(
    stationid='USW00094728',
    datatypeid='TMAX',
    startdate='2023-01-01',
    enddate='2023-12-31'
)
```

#### Documentation
- NASA: https://api.nasa.gov/
- NOAA: https://www.ncdc.noaa.gov/cdo-web/api/v2

---

### 5. Open-Meteo Weather API 🌤️

**Status:** ✅ Fully Implemented  
**Indicators:** 100+ weather variables  
**Countries:** Global  
**Data Range:** 1940-2024  
**Authentication:** None required  

#### Configuration
```env
OPEN_METEO_BASE_URL=https://api.open-meteo.com
OPEN_METEO_ENABLED=True
OPEN_METEO_RATE_LIMIT=10 per second
OPEN_METEO_CACHE_TTL=3600
```

#### Key Features
- Historical weather data
- Forecast data
- 100+ weather variables
- No API key required

#### Documentation
https://open-meteo.com/

---

## Additional Configured APIs

These APIs are configured in `.env` and ready for implementation:

### 6. UN Data API 🇺🇳
```env
UN_DATA_BASE_URL=https://data.un.org/ws/rest
UN_DATA_ENABLED=True
UN_DATA_RATE_LIMIT=5 per second
```
**Categories:** Demographics, Economics, Environment, Social statistics

### 7. Our World in Data API 📊
```env
OWID_BASE_URL=https://ourworldindata.org/api
OWID_ENABLED=True
OWID_RATE_LIMIT=5 per second
```
**Categories:** Global development, Health, Energy, Environment

### 8. IMF Data API 💰
```env
IMF_BASE_URL=https://sdmxcentral.imf.org/ws/public/sdmxapi
IMF_ENABLED=True
IMF_RATE_LIMIT=5 per second
```
**Categories:** Economic indicators, GDP, Inflation, Exchange rates

### 9. UNESCO Institute for Statistics 📚
```env
UNESCO_BASE_URL=http://uis.unesco.org/api
UNESCO_ENABLED=True
UNESCO_RATE_LIMIT=5 per second
```
**Categories:** Education, Science, Culture, Communication

### 10. ILO (International Labour Organization) 👷
```env
ILO_BASE_URL=https://www.ilo.org/ilostat/sdmx/ws/rest
ILO_ENABLED=True
ILO_RATE_LIMIT=5 per second
```
**Categories:** Employment, Wages, Labor force, Working conditions

### 11. ITU (International Telecommunication Union) 📡
```env
ITU_BASE_URL=https://data.itu.int/api
ITU_ENABLED=True
ITU_RATE_LIMIT=5 per second
```
**Categories:** ICT statistics, Internet, Mobile, Broadband

### 12. World Tourism Organization (UNWTO) ✈️
```env
UNWTO_BASE_URL=https://www.unwto.org/api
UNWTO_ENABLED=True
UNWTO_RATE_LIMIT=5 per second
```
**Categories:** Tourism statistics, Arrivals, Receipts

---

## Unified Data Schema

All API responses are normalized to a common schema:

```python
{
    "country_code": "USA",              # ISO 3166-1 alpha-3
    "country_name": "United States",     # Country name
    "indicator_code": "NY.GDP.MKTP.CD",  # Source-specific code
    "indicator_name": "GDP (current US$)", # Human-readable name
    "year": 2023,                        # Year of observation
    "value": 21000000000000.0,          # Numeric value
    "unit": "USD",                       # Unit of measurement
    "source": "world_bank",              # Source identifier
    "original_value": 21000000000000,    # Original value from source
    "original_unit": "current US$",      # Original unit
    "quality_flag": "actual",            # Quality indicator
    "last_updated": "2024-01-15T00:00:00Z", # Last update timestamp
    "metadata": {}                       # Source-specific metadata
}
```

---

## Smart Filtering

WorldInsights provides intelligent availability filtering:

### Country → Available Indicators
```python
from app.services.availability import AvailabilityService

service = AvailabilityService()

# Get indicators available for USA
indicators = service.get_available_indicators(
    country_codes=['USA', 'CHN', 'GBR']
)
```

### Indicator → Available Countries
```python
# Get countries with GDP data
countries = service.get_available_countries(
    indicator_codes=['NY.GDP.MKTP.CD']
)
```

### Intersection (Multiple Selections)
```python
# Get indicators available for ALL selected countries
indicators = service.get_available_indicators(
    country_codes=['USA', 'CHN', 'GBR', 'DEU', 'FRA']
)
```

### Availability Check
```python
# Check if data exists for specific combination
availability = service.check_availability(
    country_codes=['USA', 'CHN'],
    indicator_codes=['NY.GDP.MKTP.CD', 'SP.POP.TOTL']
)
# Returns: {
#   'available': True,
#   'missing_countries': [],
#   'missing_indicators': [],
#   'sources_with_data': ['world_bank', 'who'],
#   'data_points_estimate': 20
# }
```

---

## API Rate Limiting

WorldInsights implements token bucket rate limiting per API:

| Source | Rate Limit | Strategy |
|--------|------------|----------|
| World Bank | 10 requests/second | Token bucket |
| WHO | 5 requests/second | Token bucket |
| FAO | 5 requests/second | Token bucket |
| NASA | 10 requests/hour (DEMO_KEY) | Token bucket |
| NOAA | 5 requests/second | Token bucket |
| Open-Meteo | 10 requests/second | Token bucket |

### Rate Limiter Configuration
```python
from app.infrastructure.api_clients.base_client import TokenBucket

# Create rate limiter: 10 requests per second
rate_limiter = TokenBucket(rate=10, capacity=20)

# Consume tokens
if rate_limiter.consume():
    # Make request
    pass
else:
    # Wait for token
    rate_limiter.wait_for_token(timeout=30)
```

---

## Caching Strategy

### Multi-Layer Caching

| Layer | TTL | Backend | Purpose |
|-------|-----|---------|---------|
| API Response | 24h | Redis/In-Memory | Avoid repeated API calls |
| Availability Matrix | 1h | In-Memory | Fast country↔indicator lookup |
| DuckDB Data Lake | 7d | DuckDB | Analytics queries |

### Cache Configuration
```python
from app.infrastructure.api_clients.base_client import InMemoryCache, RedisCache

# In-memory cache (development)
cache = InMemoryCache()

# Redis cache (production)
import redis
redis_client = redis.Redis(host='localhost', port=6379)
cache = RedisCache(redis_client)
```

### Cache Hit Rates (Targets)
- API Response Cache: 80%+
- Availability Matrix: 95%+
- DuckDB Data Lake: 70%+

---

## Error Handling

### Circuit Breaker Pattern

APIs that fail repeatedly are temporarily disabled:

```python
from app.infrastructure.api_clients.base_client import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,        # Open after 5 failures
    recovery_timeout=60.0,      # Try again after 60 seconds
    half_open_max_calls=3       # Test with 3 calls
)

# Check if request allowed
if circuit_breaker.can_execute():
    # Make request
    if success:
        circuit_breaker.record_success()
    else:
        circuit_breaker.record_failure()
else:
    # Circuit is open, fail immediately
    raise Exception("Circuit breaker open")
```

### Retry Logic

Exponential backoff for failed requests:

```python
# Configured in BaseAPIClient
max_retries=3
backoff_factor=0.5

# Retry sequence: 0.5s, 1.0s, 2.0s
```

---

## Performance Benchmarks

### Response Times (Average)

| Operation | Cached | Uncached | With Retry |
|-----------|--------|----------|------------|
| Get Countries | <10ms | 200-500ms | 500-1500ms |
| Get Indicators | <10ms | 500-1000ms | 1000-3000ms |
| Get Data (single) | <10ms | 300-800ms | 800-2000ms |
| Get Data (multi) | <50ms | 1000-3000ms | 3000-8000ms |

### Throughput
- Concurrent Requests: 10-20 per second
- Daily API Calls: 100,000+ (with caching)
- Cache Hit Rate: 80%+

---

## Testing

### Mock API Responses
```python
import responses
from app.infrastructure.api_clients.world_bank import WorldBankClient

@responses.activate
def test_world_bank_client():
    # Mock API response
    responses.add(
        responses.GET,
        'https://api.worldbank.org/v2/country',
        json=[{'page': 1}, [{'id': 'USA', 'name': 'United States'}]],
        status=200
    )
    
    client = WorldBankClient()
    countries, error = client.get_countries()
    
    assert error is None
    assert len(countries) == 1
    assert countries[0]['code'] == 'USA'
```

---

## API Health Monitoring

Check status of all connected APIs:

```bash
curl http://localhost:5000/health/sources
```

Response:
```json
{
    "status": "healthy",
    "sources": {
        "world_bank": {"status": "healthy", "latency_ms": 120},
        "who": {"status": "healthy", "latency_ms": 85},
        "fao": {"status": "healthy", "latency_ms": 150},
        "nasa": {"status": "degraded", "latency_ms": 2500}
    }
}
```

---

## Getting API Keys

### NASA API Key (Free)
1. Visit https://api.nasa.gov/
2. Fill out the form
3. Receive instant API key
4. Update `.env`: `NASA_API_KEY=your_key`

### NOAA API Token (Free)
1. Visit https://www.ncdc.noaa.gov/cdo-web/token
2. Create account
3. Generate token
4. Update `.env`: `NOAA_TOKEN=your_token`

### Other APIs
Most other APIs (World Bank, WHO, FAO, UN, etc.) do **not** require authentication for basic access.

---

## Contributing

To add a new API source:

1. Create client in `app/infrastructure/api_clients/<source>.py`
2. Inherit from `BaseAPIClient`
3. Implement required methods:
   - `get_countries()`
   - `get_indicators()`
   - `get_data()`
   - `_normalize_<source>_data()`
4. Add configuration to `.env`
5. Write tests
6. Update documentation

---

## Support

For API-related issues:
- Check API documentation links above
- Review rate limits and caching settings
- Check circuit breaker status
- Enable debug logging

Contact: noreply@worldinsights.bonzainsights.com

---

**Last Updated:** 2026-03-08  
**Version:** 2.0.0
