# WorldInsights Frontend Documentation

## Overview

WorldInsights features a modern, lightweight frontend built with minimal dependencies and no build step. The frontend is designed to be easy to understand and modify, especially for Python developers.

## Architecture

### Technology Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **HTMX** | Dynamic content, AJAX without JavaScript complexity | 2.0.3 |
| **Alpine.js** | Lightweight reactive state management | 3.14.8 |
| **Plotly.js** | Interactive 2D/3D charts and visualizations | 2.32.0 |
| **Tailwind CSS** | Modern, responsive styling | 3.x (CDN) |

### Key Design Principles

1. **No Build Step** - All dependencies loaded via CDN
2. **Python-Friendly** - Templates use familiar Jinja2 syntax
3. **Progressive Enhancement** - Works without JavaScript, enhanced with it
4. **Lightweight** - Total JS payload < 100KB (gzipped)
5. **Accessible** - Semantic HTML, ARIA labels, keyboard navigation

## File Structure

```
app/
├── static/
│   ├── css/
│   │   └── styles.css          # Custom styles complementing Tailwind
│   └── js/
│       ├── api.js              # API client with caching
│       └── main.js             # Core utilities
└── templates/
    ├── base.html               # Base template with CDN includes
    ├── index.html              # Homepage
    ├── includes/
    │   ├── _navigation.html    # Responsive navbar
    │   ├── _footer.html        # Site footer
    │   └── _flash_messages.html # Flash message display
    ├── dashboard/
    │   └── builder.html        # Dashboard builder page
    ├── data_sources/
    │   ├── index.html          # Data sources overview
    │   └── indicators.html     # Indicator browser
    ├── visualization/
    │   └── globe.html          # 3D globe visualization
    └── components/
        ├── _toast.html         # Toast notification component
        ├── _loading_spinner.html # Loading states
        ├── _country_select.html # Country multi-select
        └── _indicator_select.html # Indicator selector
```

## Pages

### 1. Homepage (`/`)

**File:** `app/templates/index.html`

**Features:**
- Hero section with animated statistics
- Feature cards highlighting platform capabilities
- Data source cards with indicator counts
- Call-to-action sections

**Screenshot Description:**
- Gradient blue hero section with animated counters
- Six feature cards in a 3-column grid
- Four data source cards with icons
- Dark CTA section at bottom

### 2. Dashboard Builder (`/dashboard/builder`)

**File:** `app/templates/dashboard/builder.html`

**Features:**
- Data source selector (World Bank, WHO, FAO, NASA, Open-Meteo)
- Country multi-select with search
- Indicator selector with search and categorization
- Year range input
- Chart type selector (Line, Bar, Scatter, 3D Scatter, 3D Surface, Globe)
- Interactive Plotly chart rendering
- Save/Load dashboard functionality
- Export data (JSON/CSV)

**Screenshot Description:**
- Left sidebar with control panels
- Large chart area on right
- Modal for loading saved dashboards
- Summary statistics below chart

### 3. Data Sources (`/data-sources`)

**File:** `app/templates/data_sources/index.html`

**Features:**
- Grid of data source cards
- Search across all indicators
- Source filter tabs
- Statistics bar
- "Browse Indicators" and "Use in Dashboard" actions

**Screenshot Description:**
- Search bar at top
- Filter tabs for each source
- Statistics showing total indicators/countries
- Card grid with source details

### 4. Indicator Browser (`/data-sources/indicators`)

**File:** `app/templates/data_sources/indicators.html`

**Features:**
- Search indicators by name, code, or description
- Filter by source and category
- Sortable list (name, code, source)
- Pagination
- Add to Dashboard button
- Details modal

**Screenshot Description:**
- Left sidebar with filters
- Search bar at top
- Paginated indicator list
- Details modal on click

### 5. 3D Globe Visualization (`/visualization/globe`)

**File:** `app/templates/visualization/globe.html`

**Features:**
- Full-screen 3D globe using Plotly Mapbox
- Choropleth coloring by indicator value
- Year slider with playback animation
- Color scale selector
- Country click for details
- Zoom and pan controls

**Screenshot Description:**
- Full-screen interactive globe
- Control panel overlay on right
- Year slider with play button
- Legend showing value range

## API Integration

### API Client (`app/static/js/api.js`)

The API client provides a clean interface to the backend:

```javascript
// Get all countries
const countries = await WorldInsightsAPI.getCountries();

// Get indicators by source
const indicators = await WorldInsightsAPI.getIndicators('worldbank');

// Get plot data
const response = await WorldInsightsAPI.getData(
  ['USA', 'GBR'],           // countries
  ['NY.GDP.MKTP.CD'],       // indicators
  [2015, 2020],             // years [start, end]
  'line'                    // chart type
);

// Get globe data
const geojson = await WorldInsightsAPI.getGlobeData(
  'worldbank',
  'NY.GDP.MKTP.CD',
  2022
);

// Save dashboard
await WorldInsightsAPI.saveDashboard({
  name: 'My Dashboard',
  config: { /* ... */ }
});

// Show toast notification
WorldInsightsToast.show('Success!', 'success');
```

### Available Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `getCountries()` | Fetch all available countries | `Promise<Array>` |
| `getIndicators(source, category)` | Fetch indicators by source | `Promise<Array>` |
| `getData(countries, indicators, years, chartType)` | Fetch plot data | `Promise<Object>` |
| `getGlobeData(source, indicator, year)` | Fetch GeoJSON for globe | `Promise<Object>` |
| `getCorrelations(countries, indicators, years)` | Calculate correlations | `Promise<Object>` |
| `saveDashboard(config)` | Save dashboard config | `Promise<Object>` |
| `loadDashboard(id)` | Load saved dashboard | `Object` |
| `getSavedDashboards()` | Get all saved dashboards | `Array` |
| `deleteDashboard(id)` | Delete a dashboard | `boolean` |
| `searchIndicators(query, source)` | Search indicators | `Promise<Array>` |
| `searchCountries(query)` | Search countries | `Promise<Array>` |
| `clearCache()` | Clear API cache | `void` |

### Caching

The API client implements in-memory caching:
- **TTL:** 5 minutes (configurable)
- **Auto-cleanup:** Every 10 minutes
- **Cache key format:** `api:resource:params`

```javascript
// Check cache stats
const stats = WorldInsightsAPI.getCacheStats();
console.log(stats); // { size: 5, keys: [...] }

// Clear cache
WorldInsightsAPI.clearCache();
```

### Debouncing

Search inputs are debounced to reduce API calls:

```javascript
// Default debounce: 300ms
searchIndicators: debounce(function() {
  // Search logic
}, 300)
```

## Components

### Toast Notifications

```html
<!-- Include in base.html -->
<div id="toast-container" class="fixed top-4 right-4 z-50"></div>

<!-- Usage -->
<script>
WorldInsightsToast.show('Operation successful', 'success');
WorldInsightsToast.show('Error occurred', 'error');
WorldInsightsToast.show('Warning message', 'warning');
WorldInsightsToast.show('Info message', 'info');
</script>
```

### Loading Spinner

```html
<!-- Small spinner -->
<div class="spinner"></div>

<!-- Large spinner -->
<div class="spinner spinner-lg"></div>

<!-- With Alpine.js -->
<div x-show="isLoading">
  <svg class="animate-spin w-8 h-8 text-primary-600" ...></svg>
</div>
```

### Country Select

```html
<!-- Include component -->
{% include 'components/_country_select.html' %}

<!-- Usage with Alpine.js -->
<div x-data="{ selectedCountries: [] }">
  <div x-data="countrySelectComponent()"
       x-init="modelValue = selectedCountries"
       @country-change="selectedCountries = $event.detail.countries">
  </div>
</div>
```

### Indicator Select

```html
<!-- Include component -->
{% include 'components/_indicator_select.html' %}
```

## Styling

### Tailwind Configuration

Tailwind is configured in `base.html`:

```javascript
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: { /* ... */ },
        accent: { /* ... */ },
      },
    },
  },
};
```

### Custom CSS

Custom styles in `app/static/css/styles.css` provide:
- Animations (fade-in, slide-in, pulse)
- Component styles (cards, buttons)
- Plotly customizations
- Form element styling
- Responsive utilities
- Print styles

### Common Utility Classes

```html
<!-- Animations -->
<div class="animate-fade-in">...</div>
<div class="animate-fade-in-up">...</div>
<div class="animate-slide-in-right">...</div>

<!-- Card hover effect -->
<div class="card-hover">...</div>

<!-- Gradient text -->
<div class="gradient-text">...</div>

<!-- Glass morphism -->
<div class="glass">...</div>
```

## Development Workflow

### Running the Application

```bash
# Start the Flask development server
python run.py

# Or with gunicorn for production-like environment
gunicorn -c gunicorn_config.py run:app
```

### Making Changes

1. **Edit templates** - Modify `.html` files in `app/templates/`
2. **Edit styles** - Modify `app/static/css/styles.css`
3. **Edit JavaScript** - Modify `app/static/js/*.js`
4. **Refresh browser** - Changes are immediate (no build step)

### Debugging

```javascript
// Enable HTMX logging (already in base.html for localhost)
document.body.addEventListener('htmx:afterRequest', function(evt) {
  console.log('HTMX:', evt.detail);
});

// Check API cache
console.log(WorldInsightsAPI.getCacheStats());

// Test API calls
WorldInsightsAPI.getCountries().then(console.log);
```

## Deployment

### Static Files

All static files are served by Flask. For production:

1. **Enable caching** - Set appropriate Cache-Control headers
2. **Use CDN** - Consider serving static files from a CDN
3. **Minify** - Optionally minify CSS/JS (not required)

### Environment Variables

```bash
# .env file
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

### Performance Tips

1. **Lazy load Plotly** - Only include on pages that need it
2. **Debounce searches** - Already implemented (300ms)
3. **Cache API responses** - Already implemented (5 min TTL)
4. **Virtual scrolling** - For long lists (implemented in components)

## Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | ✅ Full |
| Firefox | 88+ | ✅ Full |
| Safari | 14+ | ✅ Full |
| Edge | 90+ | ✅ Full |

## Accessibility

- Semantic HTML elements
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus indicators
- Screen reader compatible
- Color contrast meets WCAG AA

## Troubleshooting

### Common Issues

**Charts not rendering:**
- Check if Plotly.js is loaded
- Verify container has dimensions
- Check browser console for errors

**API calls failing:**
- Check network tab for 404/500 errors
- Verify backend is running
- Check CORS settings if using different domains

**Styles not applying:**
- Verify Tailwind CDN is loaded
- Check for CSS specificity issues
- Clear browser cache

### Getting Help

1. Check browser console for errors
2. Review network requests in DevTools
3. Check Flask logs for backend errors
4. Review this documentation

## Future Enhancements

Potential improvements for future versions:

1. **Real-time updates** - WebSocket support for live data
2. **Advanced filtering** - More granular data filters
3. **Export formats** - PDF, Excel export options
4. **Collaboration** - Share dashboards with teams
5. **Mobile app** - Native mobile application
6. **Offline support** - Service worker for offline access

## Contributing

When contributing to the frontend:

1. Follow existing code patterns
2. Keep changes incremental
3. Test in multiple browsers
4. Update documentation
5. Ensure accessibility is maintained

---

**Last Updated:** March 2026  
**Version:** 1.0.0
