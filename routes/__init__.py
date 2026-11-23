"""Blueprint-и застосунку: сторінки сайту і REST API."""
from .api import api_bp
from .pages import pages_bp

__all__ = ['api_bp', 'pages_bp']
