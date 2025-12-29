# WorldInsights Backend API

## Overview

This directory contains the dedicated REST API for the WorldInsights platform. It is designed to be a modular, scalable, and professional backend service that powers the WorldInsights frontend (SPA).

## Architecture

The backend is built using **Flask** and follows a **Clean Architecture** approach:

- **`src/`**: The main source code.
  - **`api/`**: Contains the API endpoints (Controllers), organized by domain (Auth, Data, Users).
  - **`core/`**: Core logic, security context, and configuration.
  - **`services/`**: Business logic layer.
  - **`models/`**: Database models (SQLAlchemy).
- **`docs/`**: Detailed documentation for the backend system.

## Getting Started

### Prerequisites

- Python 3.9+
- Pip
- Virtual Environment (recommended)

### Installation

1.  Navigate to this directory:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Server

```bash
python run.py
```

The API will be available at `http://localhost:5001` (default).

## API Documentation

See [docs/architecture.md](docs/architecture.md) for a detailed architecture overview and [docs/sitemap.md](docs/sitemap.md) for a list of endpoints.
