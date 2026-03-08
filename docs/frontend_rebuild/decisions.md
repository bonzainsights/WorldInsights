# Architecture Decisions - Frontend Rebuild

## Decision Record: Modern Lightweight Frontend Stack

**Date**: March 8, 2026  
**Status**: Approved  
**Deciders**: WorldInsights Development Team

## Context

WorldInsights needed a frontend rebuild with the following requirements:

1. **No build steps** - No npm, webpack, vite, or complex tooling
2. **Lightweight and maintainable** - Easy for contributors to understand
3. **Interactive dashboard** - Users can plot data from APIs
4. **Improved 3D visualizations** - Better globe and chart rendering
5. **API-first approach** - Work directly with data source APIs
6. **Clean Architecture** - Separation of concerns, testable code

## Options Considered

### Option 1: React + Vite + TypeScript
**Pros:**
- Rich ecosystem
- Type safety
- Component reusability
- Large community

**Cons:**
- Requires build step (Vite)
- Complex setup for contributors
- Overkill for Flask backend
- State management complexity
- Bundle size concerns

**Verdict**: Rejected - Violates "no build step" requirement

### Option 2: Vue.js + CDN
**Pros:**
- Can work via CDN
- Gentle learning curve
- Good documentation
- Reactive by default

**Cons:**
- Still requires some JavaScript complexity
- Less suitable for server-driven UI
- Larger runtime than needed

**Verdict**: Rejected - More JavaScript than necessary

### Option 3: HTMX + Alpine.js + Plotly
**Pros:**
- No build step required
- Server-driven UI (keeps logic in Flask)
- Lightweight (~30kb total)
- Easy to understand and modify
- Progressive enhancement
- Perfect for Flask/Django backends

**Cons:**
- Smaller community than React
- Less suitable for complex SPAs
- Requires server-side rendering

**Verdict**: **SELECTED** - Best fit for requirements

### Option 4: Pure Flask + Jinja + Vanilla JS
**Pros:**
- No additional dependencies
- Simple for Flask developers
- Full control

**Cons:**
- More boilerplate for interactivity
- Reinventing wheels (AJAX, state)
- Less maintainable long-term

**Verdict**: Rejected - HTMX provides better abstraction

## Decision Details

### HTMX (Hypermedia-Driven JavaScript)

**Why HTMX:**
1. **Server-Driven UI**: Business logic stays in Python/Flask
2. **HTML Over The Wire**: Return HTML fragments, not JSON
3. **No JavaScript Framework Complexity**: Learn HTML attributes, not a framework
4. **Progressive Enhancement**: Works without JavaScript
5. **Small Footprint**: ~14kb gzipped
6. **Perfect for Flask**: Natural fit for server-rendered applications

**Key Features Used:**
- `hx-get` / `hx-post`: AJAX requests
- `hx-target`: Where to put response
- `hx-trigger`: When to make request
- `hx-swap`: How to update DOM
- `hx-indicator`: Loading states

### Alpine.js (Lightweight Reactivity)

**Why Alpine.js:**
1. **Declarative State**: `x-data`, `x-bind`, `x-on`
2. **Perfect for Small Interactions**: Dropdowns, modals, tabs
3. **No Build Step**: Works via CDN
4. **Tiny Footprint**: ~15kb gzipped
5. **Vue-like Syntax**: Familiar to many developers
6. **Complements HTMX**: HTMX for server, Alpine for client state

**Key Features Used:**
- `x-data`: Component state
- `x-bind`: Dynamic attributes
- `x-on`: Event handling
- `x-show` / `x-if`: Conditional rendering
- `x-for`: Loops
- `x-model`: Two-way binding

### Plotly.js (Visualization)

**Why Plotly:**
1. **Rich Chart Types**: 40+ including 3D
2. **Interactive**: Zoom, pan, hover, click
3. **3D Support**: Globe, surface, scatter3d
4. **Well-Documented**: Extensive examples
5. **CDN Available**: No build step
6. **Python Integration**: Works with Flask backend

**Key Features Used:**
- `Plotly.newPlot()`: Create charts
- `Plotly.react()`: Update charts
- 3D scatter, surface, globe
- Interactive legends and tooltips
- Export capabilities

### Tailwind CSS (Styling)

**Why Tailwind:**
1. **Utility-First**: Rapid UI development
2. **Responsive by Default**: Mobile-first design
3. **No Custom CSS**: Consistent design system
4. **CDN Available**: No build step (for development)
5. **Modern Design**: Clean, professional look
6. **Easy to Customize**: Configuration via script tag

**Note**: For production, consider building Tailwind to reduce file size.

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interaction                          │
│  (Select country, indicator, chart type, year range)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              HTMX Request (hx-post)                          │
│  POST /dashboard/render-chart                               │
│  { countries: ['USA'], indicator: 'NY.GDP.MKTP.CD', ... }   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Route Handler                             │
│  - Validate request                                          │
│  - Call DataFetchService                                     │
│  - Call VisualizationService                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DataFetchService                                │
│  - Select appropriate API client (WorldBankClient)          │
│  - Check cache                                               │
│  - Fetch from external API if needed                        │
│  - Normalize data                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              VisualizationService                            │
│  - Create Plotly figure                                      │
│  - Configure layout and styling                             │
│  - Convert to JSON                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              HTMX Response (JSON)                            │
│  { "chart_json": {...}, "metadata": {...} }                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Alpine.js Component                             │
│  - Receive JSON response                                     │
│  - Call Plotly.newPlot()                                     │
│  - Update UI state                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Interactive Chart                               │
│  - User can zoom, pan, hover, export                        │
└─────────────────────────────────────────────────────────────┘
```

## Clean Architecture Compliance

### Layers

1. **Delivery (Blueprints)**: Flask routes, HTMX handlers
2. **Services**: Business logic, orchestration
3. **Infrastructure**: API clients, cache, database
4. **Core**: Configuration, logging, entities

### Dependency Flow

```
Blueprints → Services → Core
    ↓           ↓
Infrastructure
```

### Key Principles

- **No business logic in routes**: Routes delegate to services
- **Type hints**: Throughout codebase
- **Docstrings**: Comprehensive documentation
- **Testable**: Services can be tested independently
- **Framework-agnostic core**: Core logic doesn't depend on Flask

## Alternatives Considered

### Server-Side Plotly Rendering
- **Considered**: Render Plotly charts as images on server
- **Rejected**: Loses interactivity, larger bandwidth

### Client-Side API Calls
- **Considered**: Call World Bank API directly from browser
- **Rejected**: CORS issues, API key exposure, rate limiting

### WebSocket for Real-time Updates
- **Considered**: Flask-SocketIO for live data
- **Rejected**: Complexity not needed for current requirements

## Consequences

### Positive

1. **Fast Development**: No build step means rapid iteration
2. **Easy Onboarding**: Contributors need only Python/HTML knowledge
3. **Small Bundle**: ~30kb total vs. 500kb+ for React apps
4. **Server Control**: Business logic stays in Python
5. **Progressive Enhancement**: Works without JavaScript
6. **Maintainable**: Clear separation of concerns

### Negative

1. **Limited SPA Features**: Not suitable for complex single-page apps
2. **Server Load**: More server-side rendering
3. **HTMX Learning Curve**: New paradigm for some developers
4. **CDN Dependency**: External resources for production

### Mitigations

1. **For complex interactions**: Use Alpine.js components
2. **For performance**: Implement caching at service layer
3. **For learning**: Comprehensive documentation provided
4. **For CDN**: Can vendor files if needed

## References

- [HTMX Documentation](https://htmx.org)
- [Alpine.js Documentation](https://alpinejs.dev)
- [Plotly.js Documentation](https://plotly.com/javascript/)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
