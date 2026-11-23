"""Перевірка JSON товару, що приходить у POST/PUT запитах.

Ті самі обмеження (LIMITS) сервер віддає клієнту через GET /api/meta,
тому валідація у браузері і на сервері завжди збігається.
Помилки повертаються словником {поле: текст}, щоб фронтенд
міг показати повідомлення біля конкретного поля форми.
"""
from models import CATEGORIES

LIMITS = {
    'name_min': 2,
    'name_max': 80,
    'price_min': 0,
    'price_max': 100000,
    'players_max': 20,
    'description_max': 500,
}


def _is_number(value):
    # bool у Python — підклас int, тому True/False явно відкидаємо
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_name(value):
    if not isinstance(value, str) or not value.strip():
        return 'Вкажіть назву гри.'
    length = len(value.strip())
    if length < LIMITS['name_min']:
        return f'Назва має містити щонайменше {LIMITS["name_min"]} символи.'
    if length > LIMITS['name_max']:
        return f'Назва може містити не більше {LIMITS["name_max"]} символів.'
    return None


def _check_price(value):
    if not _is_number(value):
        return 'Ціна має бути числом.'
    if not LIMITS['price_min'] <= value <= LIMITS['price_max']:
        return f'Ціна має бути від {LIMITS["price_min"]} до {LIMITS["price_max"]} грн.'
    return None


def _check_category(value):
    if value not in CATEGORIES:
        return 'Оберіть категорію зі списку.'
    return None


def _check_text(value, limit, label):
    if not isinstance(value, str):
        return f'Поле «{label}» має бути рядком.'
    if len(value.strip()) > limit:
        return f'Поле «{label}» може містити не більше {limit} символів.'
    return None


def validate_product(data):
    """Повертає (очищені дані, словник помилок). Якщо помилок немає — словник порожній."""
    if not isinstance(data, dict):
        return None, {'_': 'Тіло запиту має бути JSON-об\'єктом.'}

    players = data.get('players', '')
    description = data.get('description', '')
    in_stock = data.get('in_stock', True)

    errors = {
        'name': _check_name(data.get('name')),
        'price': _check_price(data.get('price')),
        'category': _check_category(data.get('category')),
        'players': _check_text(players, LIMITS['players_max'], 'Кількість гравців'),
        'description': _check_text(description, LIMITS['description_max'], 'Опис'),
        'in_stock': None if isinstance(in_stock, bool) else 'Поле in_stock має бути true або false.',
    }
    errors = {field: text for field, text in errors.items() if text}
    if errors:
        return None, errors

    clean = {
        'name': data['name'].strip(),
        'price': round(float(data['price']), 2),
        'category': data['category'],
        'players': players.strip(),
        'description': description.strip(),
        'in_stock': in_stock,
    }
    return clean, {}
