# WorldInsights - Advanced Dashboard Builder Plan

**Created:** 2026-03-08  
**Status:** Planning Phase  
**Priority:** High  

---

## 🎯 Vision

Create a **professional, interactive dashboard builder** that allows users to:
- Drag & drop movable panels to create custom layouts
- Select data sources and indicators with smart filtering
- Add text annotations, arrows, and symbols
- Create publication-ready dashboards
- Save, share, and export dashboards

---

## 📋 Requirements

### Core Features

#### 1. Movable Panel System (Canvas-Based)
- [ ] **Draggable Panels**
  - Users can drag panels anywhere on canvas
  - Snap-to-grid option (toggle)
  - Resize handles on all corners
  - Minimum/maximum size constraints
  - Panel z-index management (bring to front/send to back)

- [ ] **Panel Types**
  - Chart Panel (Plotly visualizations)
  - Text Panel (rich text annotations)
  - Image Panel (upload or URL)
  - Shape Panel (arrows, circles, rectangles)
  - KPI Panel (single metric display)
  - Spacer Panel (for layout)

- [ ] **Canvas Features**
  - Infinite canvas with pan/zoom
  - Grid background (toggle)
  - Rulers (optional)
  - Zoom controls (slider + buttons)
  - Fit to screen button
  - Canvas size presets (A4, Letter, Custom)

#### 2. Smart Data Filtering
- [ ] **Provider → Indicator → Country Cascade**
  ```
  Select Provider (WHO)
    ↓
  Show ONLY indicators available from WHO
    ↓
  Select 2+ Indicators (e.g., "Life Expectancy", "Infant Mortality")
    ↓
  Show ONLY countries that have BOTH indicators
  ```

- [ ] **Reverse Filtering**
  ```
  Select Countries (USA, Canada, UK)
    ↓
  Show ONLY indicators available for ALL selected countries
    ↓
  Select Indicator
    ↓
  Show year range available for all selections
  ```

- [ ] **Availability Matrix**
  - Pre-computed country-indicator availability
  - Real-time filtering as selections change
  - Visual indicators (✓ available, ✗ not available)
  - Count badges (e.g., "150 countries available")

#### 3. Annotation Tools
- [ ] **Text Annotations**
  - Rich text editor (bold, italic, lists, links)
  - Font size/color controls
  - Text alignment
  - Background color
  - Border options

- [ ] **Shapes & Symbols**
  - Arrows (multiple styles)
  - Circles/Ellipses
  - Rectangles
  - Lines
  - Stars, checkmarks, X marks
  - Custom icons (flag, warning, info)

- [ ] **Drawing Tools**
  - Freehand draw
  - Highlighter
  - Eraser
  - Undo/Redo

#### 4. Chart Configuration
- [ ] **Chart Types**
  - Line Chart
  - Bar Chart (vertical/horizontal)
  - Scatter Plot
  - Area Chart
  - Bubble Chart
  - Heat Map
  - 3D Surface (advanced)
  - Globe (advanced)

- [ ] **Chart Customization**
  - Title, subtitle
  - Axis labels
  - Legend position
  - Color schemes
  - Data labels (show/hide)
  - Trend lines
  - Reference lines
  - Annotations on chart

#### 5. Dashboard Management
- [ ] **Save/Load**
  - Save to database (authenticated users)
  - Save to browser localStorage (guests)
  - Load from list
  - Auto-save (every 30 seconds)
  - Version history

- [ ] **Export Options**
  - PNG (high resolution)
  - PDF (print-ready)
  - SVG (vector)
  - HTML (interactive)
  - JSON (dashboard config)

- [ ] **Sharing**
  - Generate shareable link
  - Embed code for websites
  - Public/Private toggle
  - Collaborative editing (future)

---

## 🏗️ Architecture

### Frontend Stack
```
HTMX 2.0+     → Dynamic content loading
Alpine.js 3.x → State management, drag-drop
Plotly.js     → Chart rendering
Tailwind CSS  → Styling
SortableJS    → Drag-drop (lightweight)
Interact.js   → Resizable panels (optional)
```

### Backend Services
```
Flask         → API endpoints
DuckDB        → Dashboard storage
SQLAlchemy    → ORM for dashboards
AvailabilityService → Smart filtering
PlotService   → Chart generation
```

### Data Flow
```
User Action → Alpine.js State → HTMX Request → Flask Route
    ↓
Service Layer → Availability Check → Data Fetch
    ↓
Response → HTMX Swap → DOM Update → Plotly Render
```

---

## 📐 UI/UX Design

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Navigation Bar (existing)                                   │
├──────────┬──────────────────────────────────────────┬───────┤
│          │                                          │       │
│  Data    │           CANVAS AREA                    │ Panel │
│  Panel   │         (Infinite, Draggable)            │ Props │
│          │                                          │       │
│  ┌────┐  │  ┌─────────┐  ┌──────────┐              │ ┌───┐ │
│  │WHO │  │  │ Chart 1 │  │  Text    │              │ │   │ │
│  ├────┤  │  │         │  │  Note    │              │ │   │ │
│  │Ind │  │  └─────────┘  └──────────┘              │ │   │ │
│  ├────┤  │                                          │ │   │ │
│  │Cnt │  │      ┌──────────────┐                    │ │   │ │
│  └────┘  │      │   Chart 2    │                    │ │   │ │
│          │      │              │                    │ │   │ │
│  Tools   │      └──────────────┘                    │ │   │ │
│          │                                          │ │   │ │
│  ┌────┐  │                                          │ │   │ │
│  │Text│  │                                          │ │   │ │
│  ├────┤  │                                          │ │   │ │
│  │Arrow│ │                                          │ │   │ │
│  ├────┤  │                                          │ │   │ │
│  │Shape│ │                                          │ │   │ │
│  └────┘  │                                          │ │   │ │
│          │                                          │       │
├──────────┴──────────────────────────────────────────┴───────┤
│  Status Bar: Zoom | Grid | Auto-save | Export               │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
DashboardBuilder (main)
├── DataPanel (left sidebar)
│   ├── ProviderSelector
│   ├── IndicatorSelector (with smart filtering)
│   ├── CountrySelector (with smart filtering)
│   └── YearRangeSelector
├── CanvasArea (main)
│   ├── CanvasControls (zoom, grid, fit)
│   └── DraggablePanels[]
│       ├── ChartPanel
│       ├── TextPanel
│       ├── ShapePanel
│       └── KPIPanel
├── PropertiesPanel (right sidebar)
│   ├── ChartConfig (when chart selected)
│   ├── TextConfig (when text selected)
│   └── ShapeConfig (when shape selected)
└── StatusBar (bottom)
    ├── ZoomControl
    ├── GridToggle
    ├── AutoSaveStatus
    └── ExportButtons
```

---

## 🗄️ Database Schema

### Dashboard Model
```python
class Dashboard(BaseModel):
    id: UUID
    user_id: Optional[UUID]  # Null for anonymous
    title: str
    description: Optional[str]
    layout: JSON  # Panel positions, sizes
    panels: JSON  # Panel configurations
    filters: JSON  # Selected indicators, countries, years
    created_at: datetime
    updated_at: datetime
    is_public: bool
    version: int
```

### Panel Model (embedded in Dashboard)
```python
class PanelConfig:
    id: str
    type: str  # 'chart', 'text', 'shape', 'kpi'
    position: {x: int, y: int, width: int, height: int}
    config: JSON  # Type-specific config
    z_index: int
```

---

## 📝 Implementation Plan

### Phase 1: Foundation (Week 1)
**Goal:** Basic draggable panels with data selection

1. **Day 1-2: Canvas Setup**
   - Create canvas component with pan/zoom
   - Implement grid background
   - Add zoom controls

2. **Day 3-4: Drag & Drop**
   - Integrate SortableJS or Interact.js
   - Implement panel dragging
   - Add resize handles
   - Snap-to-grid functionality

3. **Day 5: Panel Types**
   - Create ChartPanel component
   - Create TextPanel component
   - Basic panel management (add, remove, move)

4. **Day 6-7: Smart Filtering**
   - Enhance AvailabilityService
   - Create cascade filter logic
   - Implement provider → indicator → country
   - Add reverse filtering

**Deliverable:** Basic draggable panels with working data filters

---

### Phase 2: Chart Integration (Week 2)
**Goal:** Full chart customization

1. **Day 1-2: Chart Types**
   - Implement line, bar, scatter charts
   - Chart type selector
   - Data mapping UI

2. **Day 3-4: Chart Customization**
   - Title, axis labels, legend
   - Color schemes
   - Data labels toggle

3. **Day 5: Multiple Charts**
   - Support multiple chart panels
   - Independent data sources per panel
   - Panel linking (optional)

4. **Day 6-7: Testing & Refinement**
   - Test with large datasets
   - Performance optimization
   - Bug fixes

**Deliverable:** Fully customizable multi-chart dashboards

---

### Phase 3: Annotations (Week 3)
**Goal:** Rich annotation capabilities

1. **Day 1-2: Text Annotations**
   - Rich text editor
   - Font controls
   - Text panel component

2. **Day 3-4: Shapes & Symbols**
   - Arrow tool
   - Basic shapes (circle, rectangle)
   - Symbol library

3. **Day 5: Drawing Tools**
   - Freehand draw
   - Highlighter
   - Eraser

4. **Day 6-7: Integration**
   - Combine annotations with charts
   - Layer management
   - Export with annotations

**Deliverable:** Full annotation toolkit

---

### Phase 4: Dashboard Management (Week 4)
**Goal:** Save, load, export, share

1. **Day 1-2: Save/Load**
   - Database models
   - Save endpoint
   - Load dashboard list
   - Load specific dashboard

2. **Day 3: Auto-save**
   - Implement auto-save (30s interval)
   - Version history
   - Conflict resolution

3. **Day 4: Export**
   - PNG export (high-res)
   - PDF export
   - JSON export

4. **Day 5: Sharing**
   - Generate shareable links
   - Public/private toggle
   - Embed code

5. **Day 6-7: Polish**
   - UI refinement
   - Performance tuning
   - Documentation

**Deliverable:** Production-ready dashboard builder

---

## 🔧 Technical Details

### Smart Filtering Algorithm

```python
def get_available_countries(provider, indicators):
    """
    Get countries that have ALL selected indicators.
    
    Args:
        provider: Data source (e.g., 'who')
        indicators: List of indicator codes
    
    Returns:
        List of country codes
    """
    # Get availability matrix for provider
    matrix = availability_service.get_matrix(provider)
    
    # Start with countries for first indicator
    result = set(matrix.indicator_countries.get(indicators[0], []))
    
    # Intersect with remaining indicators
    for indicator in indicators[1:]:
        result &= set(matrix.indicator_countries.get(indicator, []))
    
    return sorted(list(result))


def get_available_indicators(provider, countries):
    """
    Get indicators available for ALL selected countries.
    """
    matrix = availability_service.get_matrix(provider)
    
    if not countries:
        return list(matrix.indicator_countries.keys())
    
    # Start with indicators for first country
    result = set(matrix.country_indicators.get(countries[0], []))
    
    # Intersect with remaining countries
    for country in countries[1:]:
        result &= set(matrix.country_indicators.get(country, []))
    
    return sorted(list(result))
```

### Panel State Management (Alpine.js)

```javascript
function dashboardBuilder() {
  return {
    panels: [],
    selectedPanel: null,
    canvas: {
      zoom: 1,
      panX: 0,
      panY: 0,
      showGrid: true
    },
    filters: {
      provider: null,
      indicators: [],
      countries: [],
      years: []
    },
    
    // Add new panel
    addPanel(type, config) {
      this.panels.push({
        id: `panel-${Date.now()}`,
        type,
        x: 100,
        y: 100,
        width: 400,
        height: 300,
        config,
        zIndex: this.panels.length
      });
    },
    
    // Remove panel
    removePanel(id) {
      this.panels = this.panels.filter(p => p.id !== id);
    },
    
    // Update panel position
    updatePanelPosition(id, x, y) {
      const panel = this.panels.find(p => p.id === id);
      if (panel) {
        panel.x = x;
        panel.y = y;
      }
    },
    
    // Bring to front
    bringToFront(id) {
      const maxZ = Math.max(...this.panels.map(p => p.zIndex));
      const panel = this.panels.find(p => p.id === id);
      if (panel) {
        panel.zIndex = maxZ + 1;
      }
    }
  }
}
```

---

## 📊 Success Metrics

### Performance
- Panel drag: <16ms (60fps)
- Chart render: <1s for 1000 points
- Filter response: <500ms
- Auto-save: Every 30s, <100ms

### Usability
- Time to first dashboard: <5 minutes
- Learning curve: <10 minutes
- User satisfaction: >4.5/5

### Technical
- Test coverage: >80%
- Lighthouse score: >90
- Bundle size: <200KB (gzipped)

---

## 🎯 Next Steps

1. **Review this plan** - Confirm requirements
2. **Start Phase 1** - Canvas and drag-drop
3. **Iterate** - Weekly reviews and adjustments

---

**Ready to start implementation!**

Which phase should we begin with?
