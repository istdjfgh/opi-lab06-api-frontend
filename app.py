"""Точка входу: магазин настільних ігор «Кубик» (Flask + SQLite + REST API + клієнт на fetch).

Запуск:  python app.py  ->  http://127.0.0.1:5000/api-demo
"""
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

import models
from routes import api_bp, pages_bp

API_ERROR_MESSAGES = {
    404: 'Ресурс не знайдено',
    405: 'Метод не дозволений для цієї адреси',
    500: 'Внутрішня помилка сервера. Спробуйте пізніше.',
}


def create_app(config=None):
    """Фабрика застосунку: у тестах можна передати власний шлях до БД."""
    app = Flask(__name__)
    app.config['DATABASE'] = os.environ.get('DATABASE', os.path.join(app.root_path, 'db.sqlite'))
    if config:
        app.config.update(config)

    # Кирилиця в JSON без \uXXXX, порядок ключів як у коді
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    # CORS лише для /api/*: потрібен, якщо клієнт відкривають не з цього сервера
    # (наприклад, через Live Server на порту 5500). Сама /api-demo працює і без нього.
    CORS(app, resources={r'/api/*': {'origins': '*'}})

    app.teardown_appcontext(models.close_db)
    with app.app_context():
        models.init_db()

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)
    register_error_handlers(app)

    @app.context_processor
    def inject_globals():
        return {'current_year': datetime.now().year}

    return app


def register_error_handlers(app):
    """Для /api/... помилки віддаються JSON-ом, для сайту — HTML-сторінкою."""

    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(500)
    def handle_error(err):
        code = getattr(err, 'code', 500) or 500
        if request.path.startswith('/api/'):
            return jsonify({'error': API_ERROR_MESSAGES.get(code, 'Помилка')}), code
        return render_template('error.html', code=code), code


if __name__ == '__main__':
    create_app().run(debug=True)
