---
description: WorldInsights is a global data intelligence platform aggregating open world data on population, economy, agriculture, health, climate, wealth, etc enabling researchers and users to explore, correlate, and visualize insights across countries and time
---

Its goal is to serve as a single trusted place for understanding global patterns, trends, and insights across economic, agricultural, social, health and geographical perspectives.

## 1. Core Project Vision

WorldInsights is a **global data intelligence platform** intended for:

- Researchers
- Scientists
- Policy analysts
- Students
- General users

The platform must provide:

- Reliable and verifiable global data
- Reproducible analytics and insights
- Interactive 2D and 3D visualizations
- A foundation for AI-assisted research

This project is **not** a demo, toy app, or static dashboard.

## ⚠️Rules:

- Every directory must contain `__init__.py`
- Every blueprint must live in its own subdirectory
- No business logic inside `routes.py`
- No circular dependencies

## 4. Data Source Rules (API-First Only)

### 4.1 Approved Data Sources

Initial supported data providers include:

- World Bank
- WHO
- FAO
- NASA / NOAA
- Inequality / Wealth (via adapters)

## ⚠️Rules:

- No manual downloads
- No CSVs as primary data sources
- APIs must be modular and replaceable

---

### 4.2 API Client Requirements

Every API client must:

- Live in its own file
- Implement retry logic
- Handle rate limiting
- Normalize output to the schema:
  `country | year | indicator | value | source`

- Include unit tests
- Support caching

## 5. Data Storage Rules

- Use DuckDB
- Do not store data directly in local storage as we have api ad we don't want to make our site heavy as most of the data are above 10GB
- create proper schema for raw and processed data
- ⚠️Once again we will not be storing data locally and directly channeling data from api to frontend⚠️
- Database schemas must be versioned
- Raw data is immutable

## 6. Analytics & Insights Rules

### 6.1 Analytics Engine

All analytics must:

- Be reproducible
- Be deterministic
- Be data-source agnostic
- Use Pandas, NumPy, or SciPy

---

### 6.2 Insight Requirements

Each insight must include:

- Description
- Statistical or mathematical explanation
- Input indicators
- Assumptions
- Limitations
- Unit tests

Black-box analytics are not allowed.

---

## 7. Machine Learning Rules (Phase 2+)

ML support must be modular and optional.

Rules:

- No hard-coded datasets
- Models must consume live API data
- Training pipelines must be versioned
- Models must be saved and reproducible
- Evaluation metrics must be logged

Allowed model families:

- ARIMA / SARIMA
- Prophet
- Regression
- Clustering

---

## 8. Visualization Rules (Critical)

### 8.1 2D Visualizations

- Use Plotly
- Must support dynamic filtering
- Must update automatically when data changes
- No static images

### 8.2 3D Visualizations

- A globe-based visualization is mandatory
- Users must be able to select countries
- Time-series drill-down must be supported
- Backend provides data only (no rendering)

## 9. Frontend Rules

The frontend must:

- Be responsive (mobile-first)
- Be usable by researchers and general users
- Provide clear navigation:
  - Home
  - Explore Data
  - Visualizations
  - Insights
  - About
  - Login
  - others as necessary

## 10. Authentication Rules (Mandatory from Day One)

Authentication must be implemented even if not fully enforced.

Users must be able to:

- Register -> email verification
- Login -> roles (user, researcher, admin)
- admin login have access to admin dashboard
- ⚠️Only Admin can change user's Role⚠️
- Logout

The system must be designed to support:

- Premium researcher accounts
- Saved insights and plots (future feature)

## 11. Testing Rules (No Exceptions)

### 11.1 Test-Driven Development

For every module:

1. Write tests first
2. Implement functionality
3. Run tests
4. Proceed only if tests pass

---

### 11.2 Testing Stack

- pytest
- coverage

Rules:

- No untested core logic
- No failing tests allowed
- No skipped tests without justification

---

## 12. Git & Workflow Rules (Absolute)

### 12.1 Branching

- Use `bjach` branch of `https://github.com/bonzainsights/WorldInsights.git`
- All development must happen on branch: `bjach`

---

### 12.2 Commit Rules

- Commit only after each completed module Test is Success
- Commit messages must be meaningful

Examples:

```
feat(auth): add authentication blueprint
feat(data): add World Bank API client
test(analytics): add inequality insight tests
chore: update project scaffolding
```

## 13. AI-Agent Rules (Critical)

Any AI agent working on this project must:

- Follow this document strictly
- Work incrementally
- Never dump large unstructured code
- Never bypass tests
- Reuse existing modules
- Confirm success before continuing

AI agents are contributors, not shortcuts.

---

## 14. What Is Not Allowed

- Monolithic files
- Business logic in Flask routes
- Untested analytics
- Hidden assumptions
- Hard-coded datasets
- Skipped commits
- Large code dumps
- Framework coupling in core logic

---

## 15. Final Principle

> **WorldInsights must remain scientifically credible, architecturally clean, and AI-ready.**

If a feature compromises reproducibility, modularity, testability, or explainability, it does not belong in this project.
