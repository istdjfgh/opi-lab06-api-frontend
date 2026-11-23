"""REST API магазину настільних ігор «Кубик» (JSON).

| Метод  | Адреса                 | Призначення                          |
|--------|------------------------|--------------------------------------|
| GET    | /api/health            | перевірка, що сервер працює          |
| GET    | /api/meta              | категорії, сортування, обмеження     |
| GET    | /api/products          | список (?search=&category=&sort=)    |
| GET    | /api/products/<id>     | один товар                           |
| POST   | /api/products          | створити товар                       |
| PUT    | /api/products/<id>     | повністю оновити товар               |
| DELETE | /api/products/<id>     | видалити товар                       |

Усі помилки мають один формат: {"error": "текст", "fields": {поле: текст}}.
"""
from flask import Blueprint, jsonify, request, url_for

import models
from validation import LIMITS, validate_product

api_bp = Blueprint('api', __name__, url_prefix='/api')

SORT_LABELS = {
    'newest': 'Спочатку нові',
    'oldest': 'Спочатку старі',
    'name': 'За назвою (А–Я)',
    'price_asc': 'Спочатку дешевші',
    'price_desc': 'Спочатку дорожчі',
}
MAX_SEARCH_LENGTH = 80


def error(message, status, fields=None):
    """Єдиний формат помилки для всього API."""
    body = {'error': message}
    if fields:
        body['fields'] = fields
    return jsonify(body), status


def invalid_product(errors):
    """400 з першою помилкою в `error` і всіма помилками полів у `fields`."""
    return error(next(iter(errors.values())), 400, errors)


# ------------------------------------------------------------------ службові

@api_bp.get('/health')
def health():
    return jsonify({'status': 'ok', 'time': models.now()}), 200


@api_bp.get('/meta')
def meta():
    return jsonify({
        'categories': models.CATEGORIES,
        'sort_options': [{'value': key, 'label': label} for key, label in SORT_LABELS.items()],
        'limits': LIMITS,
    }), 200


# -------------------------------------------------------------------- товари

@api_bp.get('/products')
def list_products():
    search = request.args.get('search', '').strip()[:MAX_SEARCH_LENGTH]
    category = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'newest')

    if category and category not in models.CATEGORIES:
        return error('Невідома категорія', 400)
    if sort not in models.SORT_OPTIONS:
        return error('Невідомий спосіб сортування', 400)

    return jsonify(models.list_products(search, category, sort)), 200


@api_bp.get('/products/<int:product_id>')
def get_product(product_id):
    product = models.get_product(product_id)
    if product is None:
        return error('Товар не знайдено', 404)
    return jsonify(product), 200


@api_bp.post('/products')
def create_product():
    data, errors = validate_product(request.get_json(silent=True))
    if errors:
        return invalid_product(errors)

    product = models.create_product(data)
    location = url_for('api.get_product', product_id=product['id'])
    return jsonify(product), 201, {'Location': location}


@api_bp.put('/products/<int:product_id>')
def update_product(product_id):
    if models.get_product(product_id) is None:
        return error('Товар не знайдено', 404)

    data, errors = validate_product(request.get_json(silent=True))
    if errors:
        return invalid_product(errors)

    return jsonify(models.update_product(product_id, data)), 200


@api_bp.delete('/products/<int:product_id>')
def delete_product(product_id):
    if models.get_product(product_id) is None:
        return error('Товар не знайдено', 404)
    models.delete_product(product_id)
    return '', 204
