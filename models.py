"""Робота з базою даних SQLite: підключення, схема і функції доступу до даних.

З'єднання створюється один раз на запит, зберігається в `g`
і закривається автоматично (див. `close_db`, реєструється в app.py).
Усі SQL-запити параметризовані (`?`), тому SQL-ін'єкції неможливі.
"""
import sqlite3
from datetime import datetime

from flask import current_app, g

# Категорії товарів. Список віддається клієнту через GET /api/categories,
# тому фронтенд не дублює його у своєму коді.
CATEGORIES = ['Стратегії', 'Сімейні', 'Вечірки', 'Кооперативні', 'Карткові', 'Дитячі']

# Дозволені варіанти сортування: ключ із запиту -> безпечний фрагмент SQL.
# Значення з запиту ніколи не підставляється в SQL напряму.
SORT_OPTIONS = {
    'newest': 'id DESC',
    'oldest': 'id ASC',
    'name': 'name COLLATE NOCASE ASC',
    'price_asc': 'price ASC, id DESC',
    'price_desc': 'price DESC, id DESC',
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    price       REAL    NOT NULL CHECK (price >= 0),
    category    TEXT    NOT NULL,
    players     TEXT    NOT NULL DEFAULT '',
    description TEXT    NOT NULL DEFAULT '',
    in_stock    INTEGER NOT NULL DEFAULT 1 CHECK (in_stock IN (0, 1)),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
"""

PRODUCT_FIELDS = ('name', 'price', 'category', 'players', 'description', 'in_stock')


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ---------------------------------------------------------------- з'єднання

def get_db():
    """Повертає з'єднання для поточного запиту (створює, якщо його ще немає)."""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Створює таблиці, якщо їх ще немає. Безпечно викликати повторно."""
    get_db().executescript(SCHEMA)


def row_to_dict(row):
    """Рядок БД -> словник для JSON (in_stock як справжній bool)."""
    product = dict(row)
    product['in_stock'] = bool(product['in_stock'])
    return product


# ------------------------------------------------------------------- товари

def list_products(search='', category='', sort='newest'):
    """Список товарів з необов'язковим пошуком, фільтром за категорією і сортуванням."""
    sql = 'SELECT * FROM products WHERE 1 = 1'
    params = []
    if search:
        sql += ' AND (name LIKE ? OR description LIKE ?)'
        pattern = f'%{search}%'
        params += [pattern, pattern]
    if category:
        sql += ' AND category = ?'
        params.append(category)
    sql += ' ORDER BY ' + SORT_OPTIONS.get(sort, SORT_OPTIONS['newest'])
    return [row_to_dict(row) for row in get_db().execute(sql, params).fetchall()]


def get_product(product_id):
    row = get_db().execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    return row_to_dict(row) if row else None


def create_product(data):
    """Додає товар і повертає створений запис (з id і датами)."""
    stamp = now()
    db = get_db()
    with db:  # commit при успіху, rollback при помилці
        cur = db.execute(
            'INSERT INTO products (name, price, category, players, description, in_stock, '
            'created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (*(data[field] for field in PRODUCT_FIELDS), stamp, stamp),
        )
    return get_product(cur.lastrowid)


def update_product(product_id, data):
    db = get_db()
    with db:
        db.execute(
            'UPDATE products SET name = ?, price = ?, category = ?, players = ?, '
            'description = ?, in_stock = ?, updated_at = ? WHERE id = ?',
            (*(data[field] for field in PRODUCT_FIELDS), now(), product_id),
        )
    return get_product(product_id)


def delete_product(product_id):
    db = get_db()
    with db:
        db.execute('DELETE FROM products WHERE id = ?', (product_id,))
