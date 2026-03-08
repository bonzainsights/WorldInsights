# Frontend Rebuild - WorldInsights

## Overview

This document provides a comprehensive overview of the WorldInsights frontend rebuild, transitioning from a traditional Flask+Jinja frontend to a modern, lightweight stack using **HTMX + Alpine.js + Plotly** with **Tailwind CSS** for styling.

## Project Goals

1. **Lightweight & Maintainable**: No build steps (no npm, webpack, vite)
2. **Interactive Dashboard**: Users can plot data directly from APIs
3. **Improved 3D Visualizations**: Better globe and chart visualizations
4. **API-First**: Work directly with data source APIs (no manual downloads)
5. **Contributor-Friendly**: Easy to understand and extend

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Interactivity** | HTMX 2.0+ | Dynamic content loading without JavaScript |
| **Reactivity** | Alpine.js 3.x | Lightweight client-side state management |
| **Visualization** | Plotly.js | Interactive charts and 3D visualizations |
| **Styling** | Tailwind CSS 3.x | Utility-first CSS framework |
| **Backend** | Flask 3.1+ | Python web framework |
| **Architecture** | Clean Architecture | Separation of concerns |

## Why This Stack?

### HTMX
- **No JavaScript framework complexity**: Write HTML that dynamically updates
- **Server-driven UI**: Keep business logic on the server
- **Progressive enhancement**: Works without JavaScript
- **Small footprint**: ~14kb gzipped

### Alpine.js
- **Lightweight reactivity**: ~15kb gzipped
- **Declarative syntax**: Easy to understand and maintain
- **Perfect for small interactions**: Dropdowns, modals, tabs
- **No build step required**: Works via CDN

### Plotly.js
- **Rich visualization library**: 40+ chart types
- **3D support**: Globe, surface, scatter3d
- **Interactive**: Zoom, pan, hover, click
- **Well-documented**: Extensive examples

### Tailwind CSS
- **Utility-first**: Rapid UI development
- **Responsive by default**: Mobile-first design
- **No custom CSS needed**: Consistent design system
- **CDN available**: No build step required

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (Client)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   HTMX      │  │  Alpine.js  │  │     Plotly.js       │  │
│  │  (AJAX)     │  │  (State)    │  │  (Visualizations)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                          │                                   │
│                    Tailwind CSS                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/HTMX requests
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Blueprints                            ││
│  │  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐   ││
│  │  │Dashboard │  │Visualization │  │   Data Sources  │   ││
│  │  │ Builder  │  │   (Globe)    │  │   Management    │   ││
│  │  └──────────┘  └──────────────┘  └─────────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Services Layer                        ││
│  │  ┌──────────────────┐  ┌─────────────────────────────┐ ││
│  │  │ DataFetchService │  │ VisualizationService        │ ││
│  │  └──────────────────┘  └─────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                Infrastructure Layer                     ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │WorldBankClient│  │   WHOClient │  │  FAOClient   │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  │  ┌──────────────┐  ┌──────────────┐                    ││
│  │  │  CacheLayer  │  │  RateLimiter │                    ││
│  │  └──────────────┘  └──────────────┘                    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            │ External API Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Data Sources                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ World Bank   │  │     WHO      │  │     FAO      │       │
│  │    API       │  │     API      │  │     API      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
app/
├── blueprints/
│   ├── dashboard/           # Dashboard builder blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   └── visualization/       # Visualization blueprint (updated)
│       ├── __init__.py
│       └── routes.py
├── services/
│   ├── data_fetch_service.py    # Data fetching orchestration
│   └── visualization_service.py # Chart generation
├── infrastructure/
│   └── api_clients/
│       ├── base_client.py       # Base API client
│       └── worldbank.py         # World Bank client (enhanced)
├── templates/
│   ├── base.html            # Base template (HTMX + Alpine + Plotly)
│   ├── includes/
│   │   └── _navigation.html # Modern navigation
│   └── dashboard/
│       ├── builder.html     # Dashboard builder page
│       └── components/      # Reusable components
└── static/
    ├── js/
    │   └── dashboard.js     # Dashboard-specific JS
    └── css/
        └── custom.css       # Custom styles (minimal)
```

## Key Features

### Dashboard Builder
- Select data source (World Bank, WHO, FAO, etc.)
- Choose indicators/metrics
- Select countries
- Choose year ranges
- Select chart type (line, bar, scatter, 3D scatter, 3D surface, globe)
- Render interactive Plotly charts
- Save/load custom dashboards

### 3D Globe Visualization
- Interactive 3D globe using Plotly
- Country selection on globe
- Time-series data visualization
- Zoom, rotate, click interactions

### API Integration
- World Bank API client with retry logic
- Rate limiting and caching
- Normalized data schema
- Service layer for data orchestration

## Getting Started

### Prerequisites
- Python 3.11+
- Flask 3.1+
- Internet connection (for CDN resources)

### Running the Application

```bash
# From project root
python run.py
```

The application will be available at `http://localhost:5050`

### Accessing Features

- **Dashboard Builder**: `/dashboard/builder`
- **3D Globe**: `/visualization/globe`
- **Data Sources**: `/data-sources`

## Documentation

- [Architecture Decisions](decisions.md) - Why we chose this stack
- [Implementation Log](implementation_log.md) - Step-by-step changes
- [Completed Work](completed.md) - What's finished
- [Issues & Solutions](issues.md) - Problems encountered
- [Future Work](future_work.md) - What's next

## Contributing

This frontend rebuild follows Clean Architecture principles:
- No business logic in routes
- Type hints throughout
- Comprehensive docstrings
- Well-commented code for contributors

See the main [README.md](../../README.md) for contribution guidelines.
