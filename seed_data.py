"""Наповнює базу тестовими товарами (лише якщо таблиця порожня).

Запуск:  python seed_data.py
"""
from app import create_app
import models

PRODUCTS = [
    {'name': 'Каркасон', 'price': 1150, 'category': 'Сімейні', 'players': '2–5',
     'description': 'Викладайте плитки, будуйте міста й дороги середньовічної Франції.', 'in_stock': True},
    {'name': 'Пандемія', 'price': 1490, 'category': 'Кооперативні', 'players': '2–4',
     'description': 'Командою зупиніть чотири хвороби, поки вони не охопили світ.', 'in_stock': True},
    {'name': 'Кодові імена', 'price': 690, 'category': 'Вечірки', 'players': '4–8',
     'description': 'Капітани дають підказки одним словом, команди шукають своїх агентів.', 'in_stock': True},
    {'name': 'Тераформування Марса', 'price': 2350, 'category': 'Стратегії', 'players': '1–5',
     'description': 'Корпорації змагаються за те, щоб зробити Марс придатним для життя.', 'in_stock': False},
    {'name': 'Доббль', 'price': 420, 'category': 'Дитячі', 'players': '2–8',
     'description': 'Швидка гра на уважність: знайдіть однаковий символ на двох картках.', 'in_stock': True},
    {'name': 'Вибухові кошенята', 'price': 550, 'category': 'Карткові', 'players': '2–5',
     'description': 'Карткова «російська рулетка» з котами, лазерами й козячими чарами.', 'in_stock': True},
]


def seed():
    app = create_app()
    with app.app_context():
        if models.list_products():
            print('У базі вже є товари — пропускаю.')
            return
        for product in PRODUCTS:
            models.create_product(product)
        print(f'Додано товарів: {len(PRODUCTS)}')


if __name__ == '__main__':
    seed()
