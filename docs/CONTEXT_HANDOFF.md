# WorldInsights - Context Handoff Card

**Copy this when starting a new chat to continue seamlessly**

---

## 📍 Current State

**Project:** WorldInsights - Global Data Platform  
**Branch:** `newWI`  
**Commit:** `a01d69d`  
**Location:** `/Users/achbj/Code/bonzainsights/WorldInsights`

**Status:** ✅ Backend + Frontend Complete  
**Tests:** 57/57 passing  
**Git:** Pushed to `origin/newWI`

---

## 🎯 What's Done

### Backend
- ✅ Flask app with 6 API integrations (World Bank, WHO, FAO, NASA, NOAA, Open-Meteo)
- ✅ Smart filtering (country↔indicator availability)
- ✅ Caching, rate limiting, retry logic
- ✅ 57 passing tests

### Frontend
- ✅ HTMX + Alpine.js + Plotly + Tailwind (no build step)
- ✅ Dashboard builder with save/load/export
- ✅ 3D globe visualization
- ✅ Dark/light theme with persistence
- ✅ All navigation links working
- ✅ Mobile responsive

---

## 🚀 Quick Start

```bash
cd /Users/achbj/Code/bonzainsights/WorldInsights
python run.py
```

**Access:**
- Homepage: http://localhost:5000
- Dashboard: http://localhost:5000/dashboard/builder
- 3D Globe: http://localhost:5000/visualization/globe

---

## 📚 Key Documentation

1. `docs/PROJECT_STATE.md` - Full project state (read this first)
2. `docs/FIXES_APPLIED.md` - Latest fixes (dark mode, navigation)
3. `docs/QUICKSTART.md` - Setup guide
4. `docs/MCP_SETUP.md` - MCP configuration

---

## 🔧 Current Task

**[Describe what you want to work on here]**

### Examples:
- "Add GeoJSON support for globe visualization"
- "Implement UN Data API client"
- "Add database persistence for dashboards"
- "Fix any remaining dark mode issues"

---

## 📋 Recent Changes

**Latest Commit:** `a01d69d` - Fixed dark mode toggle and navigation

- Fixed dark/light theme with localStorage persistence
- Fixed all navigation links
- Added comprehensive dark mode CSS
- Added MCP configuration
- Pushed to GitHub

---

## 🤖 MCP Status

**Configured:** Yes  
**Servers:** Filesystem, Playwright, SQLite  
**Setup:** `./scripts/setup-mcp.sh`

**Enables:**
- View screenshots
- Control browser
- Access logs
- Query databases

---

## 🎨 Design System

**Stack:** HTMX 2.0, Alpine.js 3.14, Plotly 2.32, Tailwind CSS  
**Colors:** Primary #3b82f6, Accent #22c55e  
**Dark Mode:** Full support with localStorage  
**Fonts:** Inter (sans), Space Grotesk (display)

---

## ✅ Verification

Before marking task complete:
- [ ] Code implemented
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Git committed
- [ ] Pushed to remote
- [ ] Tested in browser
- [ ] Dark mode compatible
- [ ] Mobile responsive

---

## 📞 Commands

```bash
# Run app
python run.py

# Run tests
pytest app/tests/unit/ -v

# Check status
git status

# Push changes
git add -A && git commit -m "feat: description" && git push origin newWI
```

---

**Last Updated:** 2026-03-08  
**Context Used:** ~20%  
**Next Chat:** Paste this card + describe task
