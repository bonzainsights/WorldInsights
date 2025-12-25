# WorldInsights Project Structure Guide

## Overview

WorldInsights follows **Clean Architecture** principles with a modular, scalable structure. This guide explains where files belong, how to add new features, and best practices for maintaining the codebase.

---

## 📁 Project Structure

```
WorldInsights/
├── .agent/                          # AI agent workflows and documentation
│   └── workflows/
│       └── worldinsight.md          # Project rules and guidelines
│
├── app/                             # Main application package
│   ├── blueprints/                  # Flask blueprints (routes/controllers)
│   │   ├── analytics/               # Analytics endpoints
│   │   ├── api/                     # REST API endpoints
│   │   ├── auth/                    # Authentication routes
│   │   ├── data_sources/            # Data source management
│   │   ├── frontend/                # Frontend routes
│   │   ├── ml/                      # Machine learning endpoints
│   │   └── visualization/           # Visualization endpoints
│   │
│   ├── core/                        # Framework-agnostic core logic
│   │   ├── config.py                # Configuration management
│   │   ├── logging.py               # Logging setup
│   │   └── security.py              # Security utilities
│   │
│   ├── infrastructure/              # External dependencies
│   │   ├── api_clients/             # External API clients
│   │   │   ├── worldbank.py
│   │   │   ├── who.py
│   │   │   ├── fao.py
│   │   │   └── nasa.py
│   │   ├── cache/                   # Caching layer
│   │   └── db/                      # Database layer
│   │       ├── models.py            # SQLAlchemy models
│   │       ├── database.py          # Database initialization
│   │       └── migrations/          # Database migrations
│   │
│   ├── services/                    # Business logic layer
│   │   ├── analytics_engine.py      # Analytics processing
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── data_ingestion.py        # Data ingestion logic
│   │   ├── ml_pipeline.py           # ML pipeline logic
│   │   └── subscription_service.py  # Subscription management
│   │
│   ├── static/                      # Static assets
│   │   ├── css/                     # Stylesheets
│   │   ├── js/                      # JavaScript files
│   │   └── images/                  # Images
│   │
│   ├── templates/                   # Jinja2 HTML templates
│   │   ├── auth/                    # Authentication templates
│   │   ├── base.html                # Base template
│   │   └── index.html               # Homepage
│   │
│   ├── tests/                       # Test suite
│   │   ├── fixtures/                # Test fixtures
│   │   ├── integration/             # Integration tests
│   │   └── unit/                    # Unit tests
│   │
│   ├── __init__.py                  # Package initialization
│   └── create_app.py                # Application factory
│
├── data/                            # Data storage (gitignored)
│   └── worldinsights.db             # SQLite database
│
├── docs/                            # Documentation
│   ├── requirements.md              # Project requirements
│   └── project_structure.md         # This file
│
├── logs/                            # Application logs (gitignored)
│   └── worldinsights.log
│
├── scripts/                         # Utility scripts
│   └── run_migrations.py            # Database migration runner
│
├── .env                             # Environment variables (gitignored)
├── .env.example                     # Example environment file
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── run.py                           # Development server entry point
└── wsgi.py                          # Production WSGI entry point
```

---

## 🏗️ Architecture Layers

### Layer 1: Core (Framework-Agnostic)

**Location**: `app/core/`

**Purpose**: Framework-independent business logic and utilities

**Rules**:

- ❌ NO Flask imports
- ❌ NO database imports
- ✅ Pure Python functions
- ✅ Can be used in any framework

**Example**: `security.py`

```python
# ✅ GOOD - No framework dependencies
def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# ❌ BAD - Flask dependency
from flask import current_app  # Don't do this in core!
```

---

### Layer 2: Services (Business Logic)

**Location**: `app/services/`

**Purpose**: Business logic that orchestrates core functions and infrastructure

**Rules**:

- ✅ Can import from `core/`
- ✅ Can import from `infrastructure/`
- ❌ NO Flask imports (except Flask-Mail, Flask-Login utilities)
- ✅ Returns tuples: `(result, error_message)`

**Example**: `auth_service.py`

```python
from app.core.security import hash_password, validate_password_strength
from app.infrastructure.db import db, User

def register_user(username: str, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    # Validate password
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        return None, error

    # Create user
    user = User(username=username, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()

    return user, None
```

---

### Layer 3: Infrastructure (External Dependencies)

**Location**: `app/infrastructure/`

**Purpose**: Interact with external systems (databases, APIs, cache)

**Subdirectories**:

- `api_clients/` - External API integrations
- `cache/` - Caching implementations
- `db/` - Database models and migrations

**Rules**:

- ✅ Can import framework-specific libraries
- ✅ Implements adapters for external services
- ✅ Must be replaceable (e.g., swap Redis for Memcached)

---

### Layer 4: Blueprints (Routes/Controllers)

**Location**: `app/blueprints/`

**Purpose**: HTTP request handling and response formatting

**Rules**:

- ✅ Flask-specific code lives here
- ✅ Call service layer functions
- ❌ NO business logic
- ✅ Only validate input, call services, return responses

**Example**: `auth/routes.py`

```python
from flask import render_template, request, flash
from app.blueprints.auth import auth_bp
from app.services.auth_service import register_user

@auth_bp.route('/register', methods=['POST'])
def register():
    # 1. Get input
    username = request.form.get('username')
    password = request.form.get('password')

    # 2. Call service
    user, error = register_user(username, email, password)

    # 3. Return response
    if error:
        flash(error, 'error')
        return render_template('auth/register.html')

    flash('Registration successful!', 'success')
    return redirect(url_for('auth.login'))
```

---

## 📝 How to Add New Features

### Adding a New Blueprint

**Example**: Adding a "Reports" feature

1. **Create blueprint directory**:

```bash
mkdir -p app/blueprints/reports
touch app/blueprints/reports/__init__.py
touch app/blueprints/reports/routes.py
touch app/blueprints/reports/schemas.py
touch app/blueprints/reports/README.md
```

2. **Define blueprint** (`__init__.py`):

```python
from flask import Blueprint

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

from app.blueprints.reports import routes
```

3. **Add routes** (`routes.py`):

```python
from flask import render_template
from app.blueprints.reports import reports_bp
from app.services.reports_service import generate_report

@reports_bp.route('/')
def index():
    return render_template('reports/index.html')

@reports_bp.route('/<int:report_id>')
def view_report(report_id):
    report = generate_report(report_id)
    return render_template('reports/view.html', report=report)
```

4. **Register blueprint** (`create_app.py`):

```python
from app.blueprints.reports import reports_bp
app.register_blueprint(reports_bp)
```

5. **Create service** (`services/reports_service.py`):

```python
from typing import Optional, Dict

def generate_report(report_id: int) -> Optional[Dict]:
    # Business logic here
    return {'id': report_id, 'data': [...]}
```

6. **Create templates**:

```bash
mkdir -p app/templates/reports
touch app/templates/reports/index.html
touch app/templates/reports/view.html
```

---

### Adding a New API Client

**Example**: Adding OpenAQ (Air Quality) API

1. **Create client file**:

```bash
touch app/infrastructure/api_clients/openaq.py
```

2. **Implement client**:

```python
import requests
from typing import Dict, List, Optional
from app.core.logging import get_logger

logger = get_logger('openaq_client')

class OpenAQClient:
    BASE_URL = "https://api.openaq.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-API-Key': api_key})

    def get_measurements(self, country: str, parameter: str) -> List[Dict]:
        """Fetch air quality measurements."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/measurements",
                params={'country': country, 'parameter': parameter},
                timeout=30
            )
            response.raise_for_status()
            return response.json()['results']
        except Exception as e:
            logger.error(f"Error fetching OpenAQ data: {e}")
            return []
```

3. **Add to configuration** (`core/config.py`):

```python
self._OPENAQ_API_KEY = _get_env('OPENAQ_API_KEY', None)

@property
def OPENAQ_API_KEY(self) -> Optional[str]:
    return self._OPENAQ_API_KEY
```

4. **Add to `.env.example`**:

```bash
# OpenAQ API
OPENAQ_API_KEY=your_api_key_here
```

5. **Write tests** (`tests/unit/test_openaq_client.py`):

```python
import pytest
from app.infrastructure.api_clients.openaq import OpenAQClient

def test_get_measurements():
    client = OpenAQClient()
    data = client.get_measurements('US', 'pm25')
    assert isinstance(data, list)
```

---

### Adding a Database Model

**Example**: Adding a "Report" model

1. **Add model** (`infrastructure/db/models.py`):

```python
class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='reports')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
```

2. **Create migration** (`infrastructure/db/migrations/add_reports.py`):

```python
from app.infrastructure.db import db

def upgrade():
    """Add reports table."""
    with db.engine.connect() as conn:
        conn.execute(db.text('''
            CREATE TABLE report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        '''))
        conn.commit()

def downgrade():
    """Remove reports table."""
    with db.engine.connect() as conn:
        conn.execute(db.text('DROP TABLE report'))
        conn.commit()
```

3. **Run migration**:

```bash
python scripts/run_migrations.py
```

---

### Adding Configuration Settings

1. **Add to `core/config.py`**:

```python
# In __init__
self._NEW_SETTING = _get_env('NEW_SETTING', 'default_value', str)

# Add property
@property
def NEW_SETTING(self) -> str:
    return self._NEW_SETTING

# Add to to_dict()
config_dict['NEW_SETTING'] = self._NEW_SETTING
```

2. **Add to `.env`**:

```bash
NEW_SETTING=production_value
```

3. **Add to `.env.example`**:

```bash
NEW_SETTING=default_value
```

---

## 🧪 Testing Guidelines

### Unit Tests

**Location**: `app/tests/unit/`

**Naming**: `test_<module_name>.py`

**Example**: `test_auth_service.py`

```python
import pytest
from app.services.auth_service import register_user

def test_register_user_success():
    user, error = register_user('testuser', 'test@example.com', 'SecurePass123!')
    assert user is not None
    assert error is None
    assert user.username == 'testuser'

def test_register_user_weak_password():
    user, error = register_user('testuser', 'test@example.com', 'weak')
    assert user is None
    assert 'Password must be at least 12 characters' in error
```

### Integration Tests

**Location**: `app/tests/integration/`

**Example**: `test_auth_routes.py`

```python
def test_login_route(client):
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password'
    })
    assert response.status_code == 200
```

---

## 📋 File Naming Conventions

| Type      | Convention         | Example                    |
| --------- | ------------------ | -------------------------- |
| Modules   | `snake_case.py`    | `auth_service.py`          |
| Classes   | `PascalCase`       | `UserModel`, `AuthService` |
| Functions | `snake_case()`     | `register_user()`          |
| Constants | `UPPER_SNAKE_CASE` | `MAX_LOGIN_ATTEMPTS`       |
| Templates | `snake_case.html`  | `user_profile.html`        |
| Tests     | `test_<name>.py`   | `test_auth_service.py`     |

---

## 🚫 What NOT to Do

### ❌ Don't Put Business Logic in Routes

```python
# ❌ BAD
@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    # Business logic in route - DON'T DO THIS!
    if len(password) < 12:
        flash('Password too short')
        return render_template('register.html')

    user = User(username=username, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()
```

```python
# ✅ GOOD
@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    # Call service layer
    user, error = register_user(username, email, password)

    if error:
        flash(error)
        return render_template('register.html')
```

### ❌ Don't Import Flask in Core

```python
# ❌ BAD - core/security.py
from flask import current_app

def hash_password(password: str) -> str:
    secret = current_app.config['SECRET_KEY']  # Don't do this!
```

```python
# ✅ GOOD - core/security.py
import os

def hash_password(password: str) -> str:
    secret = os.getenv('SECRET_KEY')  # Framework-agnostic
```

### ❌ Don't Create Circular Dependencies

```python
# ❌ BAD
# services/auth_service.py
from app.services.subscription_service import check_subscription

# services/subscription_service.py
from app.services.auth_service import get_user  # Circular!
```

```python
# ✅ GOOD - Move shared logic to core or create a new service
# core/user_utils.py
def get_user_by_id(user_id: int):
    return User.query.get(user_id)
```

---

## 🔄 Dependency Flow

```
┌─────────────────────────────────────────┐
│          Blueprints (Routes)            │
│         Flask-specific code             │
└──────────────┬──────────────────────────┘
               │ calls
               ▼
┌─────────────────────────────────────────┐
│      Services (Business Logic)          │
│    Orchestrates core + infrastructure   │
└──────┬───────────────────────┬──────────┘
       │                       │
       │ uses                  │ uses
       ▼                       ▼
┌──────────────┐      ┌────────────────────┐
│     Core     │      │  Infrastructure    │
│ (Pure Logic) │      │ (External Systems) │
└──────────────┘      └────────────────────┘
```

**Rules**:

- Blueprints → Services → Core/Infrastructure ✅
- Core → Infrastructure ❌
- Infrastructure → Core ✅
- Services → Blueprints ❌

---

## 📚 Quick Reference

### Adding a New Feature Checklist

- [ ] Create blueprint directory with `__init__.py`, `routes.py`, `schemas.py`
- [ ] Create service file in `app/services/`
- [ ] Add any new models to `app/infrastructure/db/models.py`
- [ ] Create database migration if needed
- [ ] Add templates to `app/templates/`
- [ ] Register blueprint in `create_app.py`
- [ ] Write unit tests in `app/tests/unit/`
- [ ] Write integration tests in `app/tests/integration/`
- [ ] Update documentation
- [ ] Run tests: `pytest`
- [ ] Commit changes

### Common Commands

```bash
# Run development server
python run.py

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/unit/test_auth_service.py

# Run migrations
python scripts/run_migrations.py

# Install dependencies
pip install -r requirements.txt

# Check code style
flake8 app/
black app/
```

---

## 🎯 Best Practices

1. **Keep functions small** - One function, one responsibility
2. **Write tests first** - TDD approach
3. **Use type hints** - Helps catch bugs early
4. **Document everything** - Docstrings for all functions
5. **Log appropriately** - Use structured logging
6. **Handle errors gracefully** - Return tuples `(result, error)`
7. **Validate input** - Never trust user input
8. **Keep secrets in .env** - Never commit secrets
9. **Follow naming conventions** - Consistency matters
10. **Review before committing** - Check diffs carefully

---

## 📖 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Best Practices](https://docs.python-guide.org/)

---

**Last Updated**: 2025-12-25  
**Version**: 1.0  
**Maintainer**: WorldInsights Team
