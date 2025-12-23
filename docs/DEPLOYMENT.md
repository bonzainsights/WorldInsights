# How to Run WorldInsights

This guide explains different ways to run the WorldInsights application.

## Development

### Using run.py (Recommended)

```bash
python run.py
```

### Custom Host/Port

```bash
FLASK_HOST=127.0.0.1 FLASK_PORT=8080 python run.py
```

### Using Flask CLI

```bash
export FLASK_APP=wsgi:app
flask run --host=0.0.0.0 --port=5000
```

## Production

### Using Gunicorn (Recommended)

**Basic:**

```bash
gunicorn wsgi:app
```

**With config file:**

```bash
gunicorn --config gunicorn_config.py wsgi:app
```

**Custom settings:**

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout 60 wsgi:app
```

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required:

- `SECRET_KEY` - Application secret key (required)

Optional:

- `FLASK_ENV` - Environment (development/production)
- `FLASK_HOST` - Host address (default: 0.0.0.0)
- `FLASK_PORT` - Port number (default: 5000)
- `LOG_LEVEL` - Logging level (default: INFO)

## Deployment Options

### Docker (Coming Soon)

```bash
docker build -t worldinsights .
docker run -p 5000:5000 --env-file .env worldinsights
```

### Platform-Specific

#### Heroku

```bash
# Procfile already configured with gunicorn
git push heroku bjach:main
```

#### Railway/Render

- Set start command: `gunicorn --config gunicorn_config.py wsgi:app`
- Add environment variables from `.env.example`

#### Traditional Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app

# Or with supervisor/systemd for process management
```

## Health Check

Once running, verify the application:

```bash
curl http://localhost:5000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "worldinsights",
  "environment": "development"
}
```
