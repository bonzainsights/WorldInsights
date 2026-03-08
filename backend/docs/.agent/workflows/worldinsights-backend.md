---
description: WorldInsights:modular Flaskbased-> ingests global data from trusted APIs stores curated indicators locally and delivers fast interactive analytics and visualizations on population, economy, agriculture, climate and health for researchers and public
---

# 🧠 WorldInsights – AI Agent Rules

## 🎯 Project Objective

Build **WorldInsights**, a modular, research-grade Flask web platform that aggregates global data from trusted APIs, stores curated indicators locally, and provides fast analytics, visualizations, and insights for researchers, students, and the public.

---

## 🏗 Architecture Rules

- Use **Flask Blueprints** for all modules.
- Each blueprint **must** live in its own subdirectory under `blueprints/`.
- Every module **must include**:
  - `__init__.py`
  - Clear docstrings
  - Unit tests
- Follow **Clean Architecture** principles.
- Use **dependency injection** where possible.
- Avoid monolithic or tightly coupled code.

---

# at start create sctructure like below and slowly we will create or changes based on necessy action as we proceed further

```
WorldInsights/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # Flask app factory
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   ├── blueprints/
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── services.py
│   │   │   │   └── tests/
│   │   │   ├── data_sources/
│   │   │   │   ├── worldbank/
│   │   │   │   │   ├── client.py
│   │   │   │   │   ├── normalizer.py
│   │   │   │   │   └── tests/
│   │   │   │   ├── who/
│   │   │   │   └── fao/
│   │   │   ├── analytics/
│   │   │   │   ├── insights.py
│   │   │   │   └── tests/
│   │   │   ├── visualization/
│   │   │   │   ├── plot_builder.py
│   │   │   │   └── tests/
│   │   │   ├── ml/
│   │   │   │   ├── pipelines/
│   │   │   │   └── tests/
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── v1/
│   │   │   │   │   ├── routes.py
│   │   │   │   │   └── schemas.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── duckdb.py
│   │   │   ├── migrations/
│   │   │   └── schemas.md
│   │   └── tests/
│   ├── requirements.txt
│   └── run.py

```

## 🌍 Data Rules

- Use **API-first ingestion only** (no manual downloads).
- Supported sources include:
  - World Bank
  - WHO
  - FAO
  - NASA / NOAA
- Normalize all ingested data to a unified schema (different for different category):
  `country | year | indicator | value | source`
- Store curated indicators locally using **DuckDB** for fast analytics.
- Separate **raw data** and **processed data**.
- Implement caching to avoid redundant API calls.
- Preserve metadata for reproducibility and traceability.

---

## 📊 Analytics & ML Rules

- Analytics must be **reproducible**, **explainable**, and **unit tested**.
- Use Pandas-based analysis.
- ML pipelines must be modular and data-agnostic.
- No hard-coded datasets.
- Persist trained models cleanly for reuse.

---

## 📈 Visualization Rules

- Use **Plotly** for interactive 2D visualizations.
- Support filters:
- Country
- Year range
- Indicator
- Enable dynamic updates when data changes.
- Prepare architecture for a future **interactive 3D globe**.
- Prioritize performance and usability.

---

## 🔐 Authentication Rules

- Implement user authentication from the start.
- Auth Rolde (user, researcher, admin)
  - by default user is registered to user
  - if user subscribed or upgrade to researcher then change to researcher
  - must be secure to hacking like if someone just tries through api and json simply sending key and values it mostnot register it as admin or researcher
- Allow public access to explore data without login for the top 10 feature/indicator and only direct api data which takes time to load other requires login and we wills set restrictions later for premium users.
- Design the system to support saved research and premium accounts in the future.

---

## 🧪 Testing & Quality Rules

- Write tests **before** implementation.
- Use `pytest` and track coverage.
- Do not proceed if tests fail.
- Maintain high code readability and documentation standards.

---

## 🔄 Git & Workflow Rules

- Work incrementally.
- Commit after each completed module.
- Use meaningful commit messages:

feat(auth): add login blueprint
test(data): add World Bank API tests

- Keep README and documentation up to date.

---

## 🚦 Execution Rules

- Never dump all code at once.
- Build and validate one module at a time.
- Confirm success before proceeding to the next stage.
- Prioritize correctness, clarity, and maintainability over speed.
