# Issues & Solutions - Frontend Rebuild

**Last Updated**: March 8, 2026

This document tracks problems encountered during the frontend rebuild and their solutions.

---

## Issue 1: HTMX Request Timeout

### Problem
HTMX requests were timing out before receiving responses from the server for large datasets.

### Symptoms
- Error message: "Request timeout"
- Chart not rendering
- Console showed 408 timeout

### Root Cause
Default HTMX timeout (30 seconds) was insufficient for complex queries with multiple countries and indicators.

### Solution
Increased HTMX timeout configuration in `base.html`:

```javascript
htmx.config.timeout = 30000; // 30 seconds
```

Also optimized the `PlotService.fetch_plot_data()` to use caching and parallel fetching.

### Status
✅ Resolved

---

## Issue 2: Alpine.js x-cloak Flash

### Problem
Alpine.js components were briefly visible before initialization, causing a flash of unstyled content.

### Symptoms
- Modal content visible on page load
- Dropdown menus briefly shown
- Poor user experience

### Root Cause
Alpine.js loads asynchronously, and elements weren't hidden before initialization.

### Solution
Added `x-cloak` attribute and CSS rule in `builder.html`:

```html
<!-- Add x-cloak to elements that should be hidden -->
<div x-show="showSaveModal" x-cloak>...</div>

<!-- CSS rule -->
<style>
[x-cloak] { display: none !important; }
</style>
```

### Status
✅ Resolved

---

## Issue 3: Plotly Chart Not Rendering in HTMX Response

### Problem
Plotly charts weren't rendering when returned as part of HTMX HTML fragments.

### Symptoms
- Empty chart container
- No errors in console
- Chart config present but not displayed

### Root Cause
Plotly's `newPlot()` requires a DOM element that exists when called. HTMX swaps content asynchronously.

### Solution
Changed approach to return JSON chart config instead of HTML, and render with Plotly in Alpine.js component after swap:

```javascript
// In Alpine component
async renderChart() {
    const response = await fetch('/dashboard/render-chart', {...});
    const data = await response.json();
    
    this.$nextTick(() => {
        if (data.chart_config && data.chart_config.data) {
            Plotly.newPlot('chart-container', 
                data.chart_config.data, 
                data.chart_config.layout, 
                data.chart_config.config
            );
        }
    });
}
```

### Status
✅ Resolved

---

## Issue 4: Country Selection Not Persisting

### Problem
Selected countries were lost when changing other parameters.

### Symptoms
- Checkboxes unchecked after indicator change
- Chart reset unexpectedly
- User frustration

### Root Cause
HTMX was re-rendering the entire country selection component instead of just updating the chart.

### Solution
Separated concerns:
- Country selection state managed by Alpine.js (client-side)
- Chart rendering triggered by Alpine.js, not HTMX
- HTMX only used for data fetching, not DOM updates

```javascript
// Alpine manages state
x-model="selectedCountries"

// Alpine triggers chart render
@change="renderChart()"
```

### Status
✅ Resolved

---

## Issue 5: Tailwind CSS Conflicts with Existing Styles

### Problem
Tailwind's preflight styles conflicted with existing `main.css` styles.

### Symptoms
- Navigation styling broken
- Buttons looked different
- Inconsistent spacing

### Root Cause
Tailwind's CSS reset was too aggressive for the existing codebase.

### Solution
Configured Tailwind to use a more limited reset and scoped custom styles:

```javascript
tailwind.config = {
    corePlugins: {
        preflight: false, // Disable full reset
    },
    // ...
};
```

Also ensured custom CSS in `main.css` has higher specificity where needed.

### Status
✅ Resolved (monitoring)

---

## Issue 6: Mobile Menu Not Closing on Route Change

### Problem
Mobile menu stayed open after clicking a navigation link.

### Symptoms
- Menu overlay persisted
- Had to manually close
- Poor mobile UX

### Root Cause
Alpine.js state wasn't being reset on navigation.

### Solution
Added `@click` handler to close menu on link click:

```html
<a href="/dashboard/builder" 
   @click="mobileMenuOpen = false"
   class="...">
    Dashboard
</a>
```

### Status
✅ Resolved

---

## Issue 7: Chart Type Selector Not Updating

### Problem
Changing chart type didn't re-render the chart.

### Symptoms
- Chart type changed in UI
- Chart remained same type
- No errors

### Root Cause
The `chartType` reactive property wasn't triggering re-render.

### Solution
Explicitly call `renderChart()` on chart type change:

```html
<button @click="chartType = type.id; renderChart()">
```

Also added debouncing to prevent rapid re-renders.

### Status
✅ Resolved

---

## Issue 8: Dashboard Save Not Working

### Problem
Saved dashboards weren't persisting.

### Symptoms
- Save appeared successful
- Load showed empty list
- Session data lost on refresh

### Root Cause
Using Flask sessions without proper secret key configuration.

### Solution
Ensured `SECRET_KEY` is set in environment:

```python
# In .env
SECRET_KEY=your-secret-key-here
```

Also added session configuration in `create_app.py`:

```python
app.config['SECRET_KEY'] = config.SECRET_KEY
```

### Status
✅ Resolved (with proper configuration)

---

## Issue 9: Globe Visualization Performance

### Problem
3D globe was slow to render with many data points.

### Symptoms
- Long loading times
- Browser lag
- Poor user experience

### Root Cause
Too many markers on the globe (200+ countries).

### Solution
1. Implemented data caching at service layer
2. Reduced marker count by filtering to countries with data
3. Used `scattergeo` instead of `choropleth` for better performance
4. Added loading indicator

### Status
✅ Improved (acceptable performance)

---

## Issue 10: Indicator Search Too Slow

### Problem
Searching through 16,000+ World Bank indicators was slow.

### Symptoms
- Search lag
- UI freeze
- Poor UX

### Root Cause
Client-side filtering of large arrays.

### Solution
1. Server-side search with limit parameter
2. Debounced search input (300ms)
3. Limited results to 100 in dropdown
4. Added "search all" link to full indicator browser

```javascript
debouncedIndicatorSearch() {
    clearTimeout(this.indicatorSearchTimer);
    this.indicatorSearchTimer = setTimeout(() => {
        this.filterIndicators();
    }, 300);
}
```

### Status
✅ Resolved

---

## Issue 11: Blueprint Import Errors

### Problem
Circular imports when registering blueprints.

### Symptoms
- `ImportError: cannot import name 'dashboard_bp'`
- Application won't start
- Circular dependency

### Root Cause
Blueprint defined and routes imported in same file.

### Solution
Separated blueprint definition from routes:

```python
# __init__.py
from flask import Blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
from . import routes  # Import after blueprint defined

# routes.py
from . import dashboard_bp  # Import blueprint
@dashboard_bp.route(...)  # Use it
```

### Status
✅ Resolved

---

## Issue 12: Type Hints Missing in Services

### Problem
Services lacked type hints, making code harder to understand.

### Symptoms
- IDE warnings
- Unclear return types
- Harder to maintain

### Root Cause
Rapid development skipped type annotations.

### Solution
Added comprehensive type hints:

```python
def create_2d_chart(
    self,
    data: List[Dict],
    chart_type: str,
    indicator: str,
    countries: List[str],
    title: Optional[str] = None
) -> Dict[str, Any]:
```

### Status
✅ Resolved

---

## Ongoing Monitoring

### Performance
- Monitor chart rendering times
- Track API response times
- Watch for memory leaks

### Browser Compatibility
- Test on Safari (sometimes lags behind)
- Mobile browser testing
- Older browser support

### Error Handling
- Add Sentry/error tracking
- Better user-facing error messages
- Graceful degradation

---

## Lessons Learned

1. **HTMX + Alpine.js is powerful**: Great combination for Flask apps
2. **JSON over HTML fragments**: Better for complex visualizations
3. **Caching is critical**: Essential for API-based data
4. **Type hints matter**: Makes maintenance much easier
5. **Documentation first**: Would have saved time
6. **Test on mobile early**: Responsive design is tricky
7. **CDN is convenient but...**: Consider vendoring for production

---

## Contact

For issues or questions about this rebuild, see the main [README.md](../../README.md).
