# 🌍 WorldInsights

**WorldInsights** is a Flask-based global data intelligence platform that brings together **free, open, and authoritative data about the world** into a single interactive research environment.

## 🎯 Project Vision

WorldInsights aggregates live and historical data from sources such as the **World Bank, FAO, WHO, NASA/NOAA**, and other open datasets to cover domains including **population, economy, GDP, agriculture, food production, literacy, geography, climate, wealth, health**, and many more.

The platform enables users to:

- Explore and combine multiple global indicators across countries and time
- Perform independent research by correlating social, economic, agricultural, and health data
- Interactively visualize data using **dynamic 2D charts** and a **3D globe**
- Drill down from global trends to country-level and time-series insights
- Experiment with data relationships

## 🏗️ Architecture

WorldInsights follows **Clean Architecture** principles:

- **Core**: Framework-agnostic business logic (config, logging, entities)
- **Services**: Application use cases and analytics engine
- **Infrastructure**: External interfaces (API clients, database, cache)
- **Delivery**: Flask blueprints and web interface

### Dependency Flow

```
Blueprints → Services → Core
    ↓           ↓
Infrastructure
```

## 📦 Tech Stack

- **Backend**: Flask 3.1.2 (Blueprints-based, API-first)
- **Database**: DuckDB 1.4.3
- **Analytics**: Pandas, NumPy, SciPy, scikit-learn
- **Visualization**: Plotly
- **Testing**: pytest, pytest-cov
- **Python**: 3.11.3 (via pyenv)

## 🚀 Quick Start

### Prerequisites

- Python 3.11.3 (recommended via pyenv)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/bonzainsights/WorldInsights.git
   cd WorldInsights
   git checkout bjach
   ```

2. **Set up Python environment**

   ```bash
   # Using pyenv (recommended)
   pyenv install 3.11.3
   pyenv local 3.11.3

   # Or use your system Python 3.11+
   python --version  # Should be 3.11.3 or compatible
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```

5. **Run tests**

   ```bash
   pytest app/tests/unit/ -v --cov=app
   ```

6. **Start the application**
   ```bash
   python -m app.create_app
   ```

The application will be available at `http://localhost:5000`

### API Endpoints

- **Health Check**: `GET /health`
- **Root**: `GET /`

## 📁 Project Structure

```
WorldInsights/
├── app/
│   ├── blueprints/          # Flask blueprints (delivery layer)
│   │   ├── analytics/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── data_sources/
│   │   ├── templates/
│   │   ├── ml/
│   │   └── visualization/
│   ├── core/                # Framework-agnostic core logic
│   │   ├── config.py       # ✅ Configuration management
│   │   ├── logging.py      # ✅ Structured logging
│   │   ├── entities.py     # Domain entities
│   │   └── interfaces.py   # Abstract interfaces
│   ├── infrastructure/      # External interfaces
│   │   ├── api_clients/    # Data source API clients
│   │   ├── cache/          # Caching layer
│   │   └── db/             # Database connections
│   ├── services/           # Application services
│   │   ├── analytics_engine.py
│   │   ├── data_ingestion.py
│   │   └── ml_pipeline.py
│   ├── templates/          # Jinja2 templates
│   ├── tests/              # Test suite
│   │   ├── fixtures/       # Test fixtures
│   │   ├── integration/    # Integration tests
│   │   └── unit/          # ✅ Unit tests (42 passing)
│   └── create_app.py      # ✅ Flask app factory
├── docs/
│   └── requirements.md     # Project requirements & rules
├── .env.example           # ✅ Environment template
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## ✅ Current Implementation Status

### Phase 1: Core Modules (COMPLETED)

- ✅ **config.py**: Environment-based configuration with validation (14 tests)
- ✅ **logging.py**: Structured logging with file rotation (15 tests)
- ✅ **create_app.py**: Flask application factory with DI (13 tests)
- ✅ **.env.example**: Environment configuration template
- ✅ **All tests passing**: 42/42 tests, 96% code coverage

### Next Steps

1. Authentication blueprint (user registration, login, email verification)
2. Data sources integration (World Bank, FAO, WHO, NASA/NOAA)
3. Analytics engine
4. Visualization blueprints
5. 3D globe visualization
6. ML pipeline (Phase 2)

## 🧪 Testing

Run all tests with coverage:

```bash
pytest app/tests/unit/ -v --cov=app/core --cov=app/create_app --cov-report=term-missing
```

Run specific test module:

```bash
pytest app/tests/unit/test_config.py -v
pytest app/tests/unit/test_logging.py -v
pytest app/tests/unit/test_create_app.py -v
```

## 🔒 Security

- **SECRET_KEY**: Required environment variable for session security
- **Email Verification**: Planned for user registration
- **Role-Based Access**: User, Researcher, Admin roles
- **CORS**: Configured for API routes

## 📝 Development Workflow

WorldInsights follows strict TDD and Clean Architecture principles:

1. **Write tests first**
2. **Implement functionality**
3. **Run tests**
4. **Commit only after tests pass**

All commits follow conventional commits:

```
feat(module): description
fix(module): description
test(module): description
docs: description
```

## 📚 Documentation

- [Full Requirements](docs/requirements.md) - Complete project specification
- [Implementation Plan](docs/implementation_plan.md) - Development roadmap

## 🤝 Contributing

This project strictly follows:

- Clean Architecture principles
- Test-Driven Development
- API-first data sources (no manual CSV uploads)
- Framework-agnostic core logic
- Incremental git commits

See [requirements.md](docs/requirements.md) for full contribution guidelines.

## 📄 License

[To be determined]

## 🔗 Links

- **Repository**: https://github.com/bonzainsights/WorldInsights
- **Active Branch**: `bjach`

---

**Built with ❤️ for researchers, scientists, and curious minds worldwide.**
