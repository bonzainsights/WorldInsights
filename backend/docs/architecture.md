# Backend Architecture

## Design Philosophy

This backend is designed with **Modularity** and **Separation of Concerns** as primary goals. It transitions WorldInsights from a monolithic Flask app (rendering HTML) to a headless **REST API**.

### Key Patterns

1.  **Application Factory**: We use a `create_app()` function in `src/__init__.py`. This allows us to create multiple instances of the app with different configurations (e.g., for testing) and prevents circular import issues.
2.  **Blueprints**: The application is divided into functional components called Blueprints.
    - `api.auth`: Handles registration, login, token refresh.
    - `api.data`: Handles data retrieval from the Data Lake.
    - `api.users`: Handles user profile management.
3.  **Service Layer**: Controllers (Routes) do not contain business logic. They call **Services**, which handle the logic and talk to **Repositories** (or directly to Models).

## Directory Structure

```
backend/
├── src/
│   ├── api/             # The Interface Layer (REST Endpoints)
│   │   ├── auth/
│   │   ├── data/
│   │   └── users/
│   ├── core/            # The Framework/Infrastructure Layer
│   │   ├── config.py    # Environment variables & App config
│   │   ├── security.py  # JWT, Password hashing
│   │   └── exceptions.py # Custom error handling
│   ├── services/        # The Application Layer (Business Logic)
│   ├── models/          # The Domain Layer (Data Structures)
│   └── __init__.py      # App Factory
├── docs/                # Documentation
└── tests/               # Automated Tests
```

## Technologies

- **Flask**: Microframework for the web server.
- **SQLAlchemy**: ORM for database interactions.
- **Flask-Migrate**: Database schema migrations.
- **Flask-Cors**: Handling Cross-Origin Resource Sharing (crucial for SPA).
- **Pydantic/Marshmallow** (Future): For request data validation.

## Data Flow

1.  **Request**: Client sends JSON to `/api/v1/auth/login`.
2.  **Route**: The `api.auth` blueprint receives the request.
3.  **Validator**: (Optional) Validates the JSON payload.
4.  **Service**: `AuthService.login_user()` is called.
5.  **Model**: Service queries `User` model.
6.  **Response**: Route returns JSON response (e.g., `{ "token": "..." }`).
