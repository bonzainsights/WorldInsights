# Backend API Sitemap

Base URL: `http://localhost:5001/api/v1` (Default)

## Authentication (`/auth`)

| Method | Endpoint | Description | Auth Required |
|d-------|----------|-------------|---------------|
| POST | `/register` | Register a new user | No |
| POST | `/login` | Login user | No |
| POST | `/logout` | Logout user | Yes |
| GET | `/me` | Get current user profile | Yes |

## Data & Visualization (`/data`)

| Method | Endpoint                               | Description               | Params                                                                      |
| ------ | -------------------------------------- | ------------------------- | --------------------------------------------------------------------------- |
| GET    | `/indicator/<source>/<indicator_code>` | Get raw indicator data    | `country` (opt), `year` (opt)                                               |
| GET    | `/globe`                               | Get GeoJSON for 3D Globe  | `source`, `indicator`, `year`                                               |
| GET    | `/plot/indicators`                     | List available indicators | -                                                                           |
| GET    | `/plot/countries`                      | List available countries  | -                                                                           |
| GET    | `/plot/data`                           | Get data for plotting     | `indicators` (comma-sep), `countries` (comma-sep), `start_year`, `end_year` |

## Health

| Method | Endpoint         | Description  |
| ------ | ---------------- | ------------ |
| GET    | `/health` (Root) | Health check |
