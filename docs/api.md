# WorldInsights API Data Sources Documentation

## Overview

WorldInsights aggregates data from **5 major free global data APIs**, providing access to economic, health, agriculture, weather, and climate indicators for 200+ countries.

---

## Data Sources Summary

| API            | Indicators | Countries | Time Range   | Auth Required | Rate Limit      |
| -------------- | ---------- | --------- | ------------ | ------------- | --------------- |
| **World Bank** | 16,000+    | 200+      | 1960-present | No            | None documented |
| **WHO**        | 10,000+    | 194       | 1990-present | Optional      | Conservative    |
| **FAO**        | 1,000+     | 245+      | 1961-present | No            | Rate limited    |
| **Open-Meteo** | 50+        | Global    | 1940-present | No            | 10K/day         |
| **NASA POWER** | 20+        | Global    | 1981-present | Yes (free)    | 1K/hour         |

---

## 1. World Bank API

### Data Coverage

**Economic Indicators:**

- GDP (current US$, constant US$, per capita, growth rate)
- GNI (Gross National Income)
- Inflation rates (consumer prices)
- Trade balance and exports/imports
- Foreign direct investment
- External debt
- Government expenditure

**Social Indicators:**

- Population (total, growth rate, density, urban/rural)
- Life expectancy at birth
- Mortality rates (infant, child, maternal)
- Literacy rates and education enrollment
- Poverty headcount ratios
- Income inequality (Gini coefficient)
- Employment and unemployment rates

**Environmental Indicators:**

- CO2 emissions (total, per capita)
- Forest area (% of land area)
- Energy use and renewable energy consumption
- Access to electricity and clean water
- Agricultural land use

**Institutional Indicators:**

- Government effectiveness
- Regulatory quality
- Rule of law
- Control of corruption
- Political stability

### Visualization Potential

**2D Visualizations:**

- ✅ Time-series line charts (GDP over time, population growth)
- ✅ Bar charts (country comparisons)
- ✅ Scatter plots (GDP vs life expectancy correlations)
- ✅ Heatmaps (regional comparisons over time)
- ✅ Area charts (stacked indicators)

**3D Visualizations:**

- ✅ Globe with country-level data (GDP, population by color/size)
- ✅ 3D surface plots (indicator evolution over time and space)
- ✅ Animated globe (time-series progression)

**Example Use Cases:**

- Track economic development across regions
- Analyze poverty trends globally
- Correlate education with economic growth
- Compare environmental sustainability metrics

---

## 2. WHO (World Health Organization) API

### Data Coverage

**Health Outcomes:**

- Life expectancy and healthy life expectancy
- Mortality rates (all causes, disease-specific)
- Morbidity and disease burden (DALYs)
- Maternal and child health indicators
- Non-communicable disease prevalence

**Disease-Specific Data:**

- Infectious diseases (HIV, TB, malaria, etc.)
- Non-communicable diseases (diabetes, cancer, cardiovascular)
- Mental health indicators
- Vaccine-preventable diseases

**Health Systems:**

- Health workforce density (doctors, nurses per 10,000)
- Hospital beds and health facilities
- Health expenditure (public, private, out-of-pocket)
- Universal health coverage metrics

**Risk Factors:**

- Tobacco use prevalence
- Alcohol consumption
- Obesity and overweight rates
- Physical inactivity
- Air pollution exposure

### Visualization Potential

**2D Visualizations:**

- ✅ Time-series (disease trends, life expectancy improvements)
- ✅ Choropleth maps (disease prevalence by country)
- ✅ Comparative bar charts (health system metrics)
- ✅ Bubble charts (health expenditure vs outcomes)

**3D Visualizations:**

- ✅ Globe with health indicators (life expectancy, disease burden)
- ✅ 3D scatter plots (multi-dimensional health analysis)
- ⚠️ Limited geographic granularity (country-level only)

**Example Use Cases:**

- Track global disease outbreaks
- Analyze health system performance
- Correlate health expenditure with outcomes
- Monitor progress toward SDG health targets

---

## 3. FAO (Food and Agriculture Organization) API

### Data Coverage

**Agricultural Production:**

- Crop production (cereals, fruits, vegetables)
- Livestock production (meat, milk, eggs)
- Fisheries and aquaculture
- Forestry products

**Food Security:**

- Food supply (calories, protein per capita)
- Undernourishment prevalence
- Food price indices
- Food import dependency

**Land and Resources:**

- Agricultural land area
- Irrigated land
- Fertilizer use
- Pesticide use
- Water use in agriculture

**Trade:**

- Agricultural exports and imports
- Trade values and quantities
- Self-sufficiency ratios

### Visualization Potential

**2D Visualizations:**

- ✅ Production trends over time
- ✅ Trade flow diagrams
- ✅ Food security heatmaps
- ✅ Comparative crop yields

**3D Visualizations:**

- ✅ Globe with agricultural production data
- ⚠️ Limited - primarily country-level aggregates
- ✅ 3D bar charts for multi-country comparisons

**Example Use Cases:**

- Monitor global food production trends
- Analyze food security vulnerabilities
- Track agricultural trade patterns
- Assess environmental impact of agriculture

---

## 4. Open-Meteo API

### Data Coverage

**Weather Variables:**

- Temperature (mean, max, min at 2m height)
- Precipitation (rain, snow)
- Wind speed and direction
- Relative humidity
- Cloud cover
- Solar radiation
- Atmospheric pressure

**Time Ranges:**

- Historical data (1940-present)
- Weather forecasts (up to 16 days)
- Climate projections

**Spatial Coverage:**

- Global coverage at ~11km resolution
- Point-based queries (latitude/longitude)
- No country aggregation (capital cities used as proxy)

### Visualization Potential

**2D Visualizations:**

- ✅ Temperature time-series
- ✅ Precipitation patterns
- ✅ Weather comparison charts
- ✅ Climate trend analysis

**3D Visualizations:**

- ✅ Globe with temperature/precipitation overlays
- ✅ Animated weather patterns over time
- ✅ 3D surface plots of climate variables
- ⚠️ Point-based data (not country polygons)

**Example Use Cases:**

- Analyze climate change trends
- Compare weather patterns across cities
- Track extreme weather events
- Correlate weather with agricultural yields

---

## 5. NASA POWER API

### Data Coverage

**Solar Energy:**

- Solar irradiance (direct, diffuse, global)
- Photovoltaic potential
- Solar noon time

**Meteorological Data:**

- Temperature (2m, surface)
- Precipitation
- Wind speed and direction
- Relative humidity
- Atmospheric pressure
- Cloud cover

**Temporal Resolution:**

- Daily, monthly, annual averages
- Data from 1981-present
- Near real-time updates

**Spatial Coverage:**

- Global coverage at 0.5° x 0.5° resolution
- Point-based queries
- Capital cities used as country proxy

### Visualization Potential

**2D Visualizations:**

- ✅ Solar potential maps
- ✅ Temperature and precipitation trends
- ✅ Energy resource assessment charts

**3D Visualizations:**

- ✅ Globe with solar irradiance data
- ✅ 3D climate variable surfaces
- ⚠️ Point-based (not country-level)

**Example Use Cases:**

- Assess renewable energy potential
- Climate analysis for agriculture
- Long-term climate trend analysis
- Correlate solar radiation with crop yields

---

## Data Integration Strategy

### Standard Schema

All data sources are normalized to a common schema:

```python
{
    'country': str,        # ISO 3166-1 alpha-3 code (e.g., 'USA')
    'year': int,           # Year of observation
    'indicator': str,      # Indicator/variable code
    'value': float,        # Numeric value (None if missing)
    'source': str,         # Data source name
    'date': str           # Optional: full date for daily data (YYYY-MM-DD)
}
```

### Data Aggregation

**Country-Level Data:**

- World Bank: Native country-level aggregates ✅
- WHO: Native country-level aggregates ✅
- FAO: Native country-level aggregates ✅
- Open-Meteo: Capital city as proxy ⚠️
- NASA POWER: Capital city as proxy ⚠️

**Temporal Aggregation:**

- Daily data can be aggregated to monthly/yearly
- Yearly data is primary format for most sources
- Time-series analysis supported across all sources

---

## Visualization Recommendations

### 2D Visualizations (Plotly)

**Recommended Chart Types:**

1. **Time-Series Line Charts**

   - Best for: Economic trends, population growth, climate change
   - Data sources: All
   - Example: GDP growth over 50 years

2. **Choropleth Maps**

   - Best for: Geographic comparisons at a point in time
   - Data sources: World Bank, WHO, FAO
   - Example: Life expectancy by country in 2020

3. **Scatter Plots**

   - Best for: Correlation analysis
   - Data sources: All (cross-source analysis)
   - Example: GDP per capita vs life expectancy

4. **Bar Charts**

   - Best for: Country comparisons
   - Data sources: All
   - Example: Top 10 countries by renewable energy use

5. **Heatmaps**
   - Best for: Multi-dimensional comparisons
   - Data sources: All
   - Example: Health indicators across regions over time

### 3D Visualizations (Globe + Three.js/Plotly)

**Recommended Visualizations:**

1. **Interactive Globe with Country Data**

   - Color-code countries by indicator value
   - Size bubbles by population or GDP
   - Click for time-series drill-down
   - Data sources: World Bank, WHO, FAO

2. **Animated Time-Series Globe**

   - Show indicator evolution over time
   - Play/pause controls
   - Data sources: All

3. **3D Surface Plots**

   - X: Countries, Y: Years, Z: Indicator value
   - Useful for trend visualization
   - Data sources: All

4. **Weather/Climate Globe Overlays**
   - Temperature/precipitation heat maps
   - Real-time weather visualization
   - Data sources: Open-Meteo, NASA POWER

**Limitations:**

- Weather APIs provide point data (not country polygons)
- Requires interpolation or capital city representation
- Best suited for 2D maps with point markers

---

## Analytics Opportunities

### Cross-Source Analysis

**Economic + Health:**

- Correlate GDP with life expectancy
- Analyze health expenditure efficiency
- Track development progress (HDI-like metrics)

**Agriculture + Climate:**

- Correlate crop yields with weather patterns
- Analyze climate impact on food security
- Predict agricultural productivity

**Environment + Development:**

- Track CO2 emissions vs economic growth
- Analyze renewable energy adoption
- Monitor sustainable development goals

### Machine Learning Potential

**Forecasting:**

- Economic growth predictions (ARIMA, Prophet)
- Disease outbreak prediction (time-series models)
- Climate trend forecasting

**Clustering:**

- Group countries by development patterns
- Identify similar health system profiles
- Classify agricultural economies

**Anomaly Detection:**

- Identify unusual economic shocks
- Detect disease outbreaks early
- Flag extreme weather events

---

## Implementation Roadmap

### Phase 1: Data Exploration (CURRENT)

- ✅ Implement all 5 API clients
- ✅ Verify data access and quality
- ✅ Document data schemas

### Phase 2: Frontend Development (NEXT)

- [ ] Create `/explore` page for data browsing
- [ ] Implement indicator selection UI
- [ ] Add country and year filtering
- [ ] Display data in tables

### Phase 3: 2D Visualizations

- [ ] Integrate Plotly for interactive charts
- [ ] Implement time-series line charts
- [ ] Add choropleth maps
- [ ] Create scatter plots for correlations
- [ ] Build comparative bar charts

### Phase 4: 3D Globe Visualization

- [ ] Implement interactive 3D globe
- [ ] Add country selection and highlighting
- [ ] Integrate indicator data overlay
- [ ] Add time-series animation controls
- [ ] Enable drill-down to detailed charts

### Phase 5: Analytics Engine

- [ ] Implement correlation analysis
- [ ] Add trend detection
- [ ] Create statistical summaries
- [ ] Build comparison tools

### Phase 6: Machine Learning

- [ ] Implement forecasting models
- [ ] Add clustering analysis
- [ ] Create anomaly detection
- [ ] Build recommendation engine

---

## Technical Considerations

### Performance

- Implement caching layer (Redis/in-memory)
- Lazy-load data on demand
- Paginate large result sets
- Pre-aggregate common queries

### Data Quality

- Handle missing values gracefully
- Validate data ranges
- Flag outliers and anomalies
- Document data limitations

### User Experience

- Progressive data loading
- Clear loading indicators
- Error messages with suggestions
- Export functionality (CSV, JSON)

### Scalability

- Rate limit API calls
- Queue background data fetches
- Cache API responses
- Consider bulk data downloads for FAO

---

## Summary

WorldInsights now has access to **27,000+ indicators** across **5 data sources**, covering:

- 📊 Economic development (World Bank)
- 🏥 Global health (WHO)
- 🌾 Agriculture & food security (FAO)
- 🌤️ Weather & climate (Open-Meteo, NASA POWER)

**Next Priority:** Build data exploration UI to make this data accessible and visualizable for users.
