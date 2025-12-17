# WorldInsights: Project Guide & Architecture

## 1. Executive Summary

**WorldInsights** is a web application designed to be a comprehensive hub for global data visualization. It serves both general users and researchers by providing interactive, easy-to-digest insights into complex datasets (Population, GDP, Agriculture, Health).

## 2. Technology Stack

### Backend: Python & Flask

- **Framework**: **Flask**. chosen for its flexibility and lightweight nature. It allows us to build a custom structure without the overhead of Django.
- **Language**: **Python 3.x**. Excellent for data manipulation (Pandas, NumPy) and API integration.
- **Data Processing**: `pandas` for cleaning and structuring data before sending it to the frontend.
- **Caching**: `Flask-Caching` (using simple in-memory or filesystem cache initially) to avoid hitting external APIs constantly and improve speed.

### Frontend: Modern Web Technologies

- **Structure**: HTML5 (Jinja2 Templates).
- **Styling**: Vanilla CSS with a focus on modern aesthetics (Glassmorphism, Dark Mode, Responsive Grid).
- **Interactivity**:
  - **Globe Visualization**: **Globe.gl** (based on Three.js). It is optimized for data visualization on a globe and easiest to implement for "World Insights".
  - **Charts/Graphs**: **Chart.js** or **Apache ECharts** for robust statistical plotting.

### Data Sources (APIs)

- **Core Data**: **World Bank API**. Covers 90% of requirements (GDP, Population, Agriculture, Health, Education). Easy to use via the `wbdata` Python library or direct REST calls.
- **Food/Agriculture**: **FAOSTAT** (if World Bank data is insufficient).
- **Health**: **WHO (Global Health Observatory)** APIs.
- **GeoJSON**: Natural Earth data for country boundaries (required for 3D globe choropleths).

## 3. Project Structure

We will use the **Application Factory Pattern** to ensure the app is scalable and testable.

```text
WorldAnalytics/
├── app/
│   ├── __init__.py          # App initialization & factory function
│   ├── main/                # Main Blueprint (Routes for pages)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── api/                 # API Blueprint (Internal endpoints for tools)
│   │   ├── __init__.py
│   │   └── data_routes.py   # Fetches data from WorldBank and serves JSON to front
│   ├── models.py            # Database models (if we add user accounts)
│   ├── services/            # Logic layer
│   │   └── world_bank.py    # Wrapper for external API calls
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   └── globe.css
│   │   ├── js/
│   │   │   ├── globe_init.js
│   │   │   └── charts.js
│   │   └── img/
│   └── templates/
│       ├── _layout.html     # Base template
│       ├── index.html       # 3D Globe View
│       └── dashboard.html   # Detailed stats view
├── config.py                # Configuration (API Keys, Debug modes)
├── requirements.txt         # Python dependencies
└── run.py                   # Entry point
```

## 4. Feature Roadmap

### Phase 1: Foundation

- Setup Flask App Factory.
- Implement `wbdata` integration to fetch basic "Population" stats.
- Create a basic Homepage with a 3D Earth using Globe.gl.

### Phase 2: Core Data Layers

- **Interactive Globe**: Hovering over a country shows a tooltip with live API data.
- **Data Selectors**: Allow users to switch between "Population", "GDP", and "CO2 Emissions".
- **Backend Caching**: Ensure fast load times.

### Phase 3: Research Tools

- **Comparison View**: Select two countries to compare side-by-side charts.
- **Historical Trends**: Line charts showing change over 10-20 years.

### Phase 4: Advanced (Health & Soil)

- Integrate detailed health datasets.
- Add granular agricultural data (if available via API).

## 5. Next Steps

1.  Initialize the folder structure.
2.  Install `flask`, `wbdata`, `requests`.
3.  Create the `run.py` and `app/__init__.py` to get a "Hello World" running.
