# Future Work - Frontend Rebuild

**Last Updated**: March 8, 2026  
**Priority**: High → Low

This document outlines planned enhancements and future work for the WorldInsights frontend rebuild.

---

## Phase 2: Enhanced Features (Q2 2026)

### 2.1 Database Persistence for Dashboards 🔴 HIGH

**Current State**: Dashboards saved to Flask session (lost on browser close)

**Planned**:
- Create `Dashboard` model in database
- User-specific dashboard storage
- Dashboard sharing (public/private)
- Dashboard versioning

**Implementation**:
```python
# models/dashboard.py
class Dashboard(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    config = db.Column(db.JSON)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
```

**Estimated Effort**: 2-3 days

---

### 2.2 Additional Chart Types 🟡 MEDIUM

**Current**: Line, bar, scatter, 3D scatter, 3D surface, globe

**Planned Additions**:
- **Area charts**: Stacked area for cumulative data
- **Heatmaps**: Country-indicator matrices
- **Treemaps**: Hierarchical data visualization
- **Sankey diagrams**: Flow visualization
- **Time series with forecasting**: ARIMA predictions

**Implementation**: Add to `VisualizationService.create_*_chart()` methods

**Estimated Effort**: 3-4 days

---

### 2.3 Dashboard Templates 🟡 MEDIUM

**Current**: Users build from scratch

**Planned**:
- Pre-built dashboard templates
- "GDP Comparison" template
- "Health Indicators" template
- "Climate Data" template
- One-click template application

**Implementation**:
```python
# services/dashboard_templates.py
TEMPLATES = {
    'gdp_comparison': {
        'name': 'GDP Comparison',
        'indicators': ['NY.GDP.MKTP.CD'],
        'chart_type': 'line',
        'countries': ['USA', 'CHN', 'JPN', 'DEU', 'GBR']
    },
    # ...
}
```

**Estimated Effort**: 1-2 days

---

### 2.4 Data Export 🟡 MEDIUM

**Current**: No export functionality

**Planned**:
- Export chart as PNG/SVG
- Export data as CSV
- Export dashboard config as JSON
- Print-friendly view

**Implementation**:
```javascript
// In dashboard builder
exportChart(format) {
    if (format === 'png') {
        Plotly.downloadImage('chart-container', {format: 'png'});
    } else if (format === 'csv') {
        // Convert data to CSV and download
    }
}
```

**Estimated Effort**: 1-2 days

---

### 2.5 Comparison Mode 🟡 MEDIUM

**Current**: Single indicator visualization

**Planned**:
- Side-by-side chart comparison
- Different indicators, same countries
- Different countries, same indicator
- Synchronized zoom/pan

**Implementation**: Multi-chart layout in dashboard builder

**Estimated Effort**: 2-3 days

---

## Phase 3: Performance & Optimization (Q3 2026)

### 3.1 Caching Improvements 🔴 HIGH

**Current**: Basic in-memory caching via `plot_service`

**Planned**:
- Redis caching layer
- Cache warming for popular indicators
- Cache invalidation strategies
- Per-user cache quotas

**Implementation**:
```python
# infrastructure/cache/redis_cache.py
class RedisCache:
    def __init__(self):
        self.redis = Redis.from_url(config.REDIS_URL)
    
    def get_chart(self, key: str) -> Optional[Dict]:
        data = self.redis.get(f"chart:{key}")
        return json.loads(data) if data else None
```

**Estimated Effort**: 2-3 days

---

### 3.2 API Response Optimization 🟡 MEDIUM

**Current**: Fetch all data, then filter

**Planned**:
- Server-side filtering
- Pagination for large datasets
- Streaming responses
- GraphQL-like query language

**Implementation**:
```python
# Optimize fetch_plot_data
def fetch_plot_data(self, indicators, countries, start_year, end_year, limit=None):
    # Add LIMIT to SQL query
    # Use server-side aggregation
```

**Estimated Effort**: 3-4 days

---

### 3.3 Frontend Performance 🟡 MEDIUM

**Current**: All CDN resources loaded on every page

**Planned**:
- Bundle critical CSS
- Lazy load Plotly for non-visualization pages
- Service worker for offline support
- Image optimization

**Implementation**:
```html
<!-- Load Plotly only when needed -->
<script>
if (window.location.pathname.startsWith('/dashboard')) {
    const script = document.createElement('script');
    script.src = 'https://cdn.plot.ly/plotly-2.30.0.min.js';
    document.head.appendChild(script);
}
</script>
```

**Estimated Effort**: 2-3 days

---

### 3.4 Progressive Web App (PWA) 🟢 LOW

**Current**: Standard web app

**Planned**:
- Service worker
- Offline support for saved dashboards
- Add to home screen
- Push notifications for data updates

**Implementation**: Add `manifest.json` and service worker

**Estimated Effort**: 2-3 days

---

## Phase 4: User Experience (Q4 2026)

### 4.1 User Authentication Integration 🔴 HIGH

**Current**: Session-based, no auth required

**Planned**:
- Login required for save/load
- User-specific dashboards
- Dashboard sharing
- Collaborative dashboards

**Implementation**: Integrate with existing `auth` blueprint

**Estimated Effort**: 2-3 days

---

### 4.2 Dashboard Sharing 🟡 MEDIUM

**Current**: Private to session

**Planned**:
- Public dashboard URLs
- Embed codes for external sites
- Social sharing (Twitter, LinkedIn)
- Dashboard gallery

**Implementation**:
```python
@dashboard_bp.route('/shared/<dashboard_id>')
def shared_dashboard(dashboard_id):
    dashboard = Dashboard.query.get(dashboard_id)
    if dashboard.is_public:
        return render_template('dashboard/shared.html', dashboard=dashboard)
```

**Estimated Effort**: 2-3 days

---

### 4.3 Annotations & Notes 🟢 LOW

**Current**: No annotation support

**Planned**:
- Add notes to charts
- Highlight specific data points
- Chart annotations
- Export with annotations

**Implementation**: Plotly annotation API

**Estimated Effort**: 1-2 days

---

### 4.4 Alerts & Notifications 🟢 LOW

**Current**: No alerts

**Planned**:
- Set data thresholds
- Email alerts when data updates
- Dashboard change notifications

**Implementation**: Background job + email service

**Estimated Effort**: 3-4 days

---

## Phase 5: Advanced Features (2027)

### 5.1 Machine Learning Integration 🟡 MEDIUM

**Planned**:
- Trend forecasting
- Anomaly detection
- Clustering similar countries
- Correlation suggestions

**Implementation**: Integrate with `ml_pipeline.py`

**Estimated Effort**: 5-7 days

---

### 5.2 Natural Language Queries 🟢 LOW

**Planned**:
- "Show me GDP for USA and China"
- "Compare life expectancy in Europe"
- AI-powered query interpretation

**Implementation**: LLM integration

**Estimated Effort**: 7-10 days

---

### 5.3 Real-time Data 🟢 LOW

**Planned**:
- WebSocket for live updates
- Real-time weather data
- Stock market indicators
- Live collaboration

**Implementation**: Flask-SocketIO

**Estimated Effort**: 3-4 days

---

## Technical Debt

### 5.1 Unit Tests 🔴 HIGH

**Current**: No tests for new code

**Planned**:
- Test `VisualizationService`
- Test dashboard routes
- Test data transformation
- Integration tests

**Implementation**:
```python
# app/tests/unit/test_visualization_service.py
def test_create_line_chart():
    service = VisualizationService()
    config = service.create_2d_chart(data, 'line', 'TEST', ['USA'])
    assert config['data'][0]['type'] == 'scatter'
```

**Estimated Effort**: 3-4 days

---

### 5.2 API Documentation 🟡 MEDIUM

**Current**: No API docs for new endpoints

**Planned**:
- OpenAPI/Swagger spec
- Interactive API docs
- Example requests/responses

**Implementation**: Flask-RESTX or similar

**Estimated Effort**: 1-2 days

---

### 5.3 Error Tracking 🟡 MEDIUM

**Current**: Basic logging

**Planned**:
- Sentry integration
- Error dashboards
- Alert on critical errors

**Implementation**: Sentry SDK

**Estimated Effort**: 0.5 days

---

### 5.4 Performance Monitoring 🟡 MEDIUM

**Current**: No monitoring

**Planned**:
- Request timing
- Chart render times
- API latency tracking
- User analytics

**Implementation**: Prometheus + Grafana or similar

**Estimated Effort**: 1-2 days

---

## Documentation Improvements

### 6.1 Contributor Guide 🟡 MEDIUM

**Planned**:
- How to add new chart types
- How to add data sources
- Coding standards
- PR template

**Location**: `docs/CONTRIBUTING.md`

---

### 6.2 API Client Templates 🟢 LOW

**Planned**:
- Template for new API clients
- Example implementations
- Testing guidelines

**Location**: `docs/api_client_template.md`

---

## Backlog (Nice to Have)

- [ ] Dark mode toggle
- [ ] Custom color schemes
- [ ] Dashboard drag-and-drop layout
- [ ] Video tutorials
- [ ] Interactive walkthrough
- [ ] Keyboard shortcuts
- [ ] Multi-language support
- [ ] Accessibility improvements (WCAG 2.1)
- [ ] Print stylesheets
- [ ] Email dashboard reports

---

## Priority Matrix

```
                    ┌─────────────────┬─────────────────┐
                    │   HIGH IMPACT   │   LOW IMPACT    │
        ┌───────────┼─────────────────┼─────────────────┤
        │   EASY    │ 1. DB Persist   │ 2. PWA          │
        │           │ 3. Auth Integ   │ 4. Annotations  │
        ├───────────┼─────────────────┼─────────────────┤
        │   HARD    │ 5. Caching      │ 6. ML Features  │
        │           │ 7. Performance  │ 8. NLP Queries  │
        └───────────┴─────────────────┴─────────────────┘
```

---

## Getting Involved

Want to contribute to any of these features?

1. Check out the project: `git clone https://github.com/bonzainsights/WorldInsights.git`
2. Read the docs: `docs/frontend_rebuild/README.md`
3. Pick an issue from this list
4. Create a branch: `git checkout -b feature/your-feature`
5. Submit a PR!

---

## Questions?

See the main [README.md](../../README.md) for contact information.
