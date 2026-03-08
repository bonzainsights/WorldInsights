"""
Data Sources Blueprint for WorldInsights.

This blueprint provides data source management functionality, allowing users to:
- View available data sources
- Browse indicators by source
- Check data source status
- Refresh data source caches

Following Clean Architecture:
- This is the delivery layer (Flask-specific)
- Delegates to services for business logic
- Returns JSON for HTMX consumption
"""
from flask import Blueprint

data_sources_bp = Blueprint('data_sources', __name__, url_prefix='/data-sources')

from . import routes
