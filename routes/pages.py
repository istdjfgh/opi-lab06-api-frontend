"""HTML-сторінки сайту. Дані на /api-demo підтягує JavaScript через REST API."""
from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)


@pages_bp.get('/')
def home():
    return render_template('home.html')


@pages_bp.get('/api-demo')
def api_demo():
    """Клієнтська частина: список, пошук, додавання, редагування й видалення товарів через fetch()."""
    return render_template('api-demo.html')


@pages_bp.get('/about')
def about():
    return render_template('about.html')
