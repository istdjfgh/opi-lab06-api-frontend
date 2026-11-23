"""Спільні фікстури: застосунок з окремою тимчасовою базою для кожного тесту."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

VALID_PRODUCT = {
    'name': 'Каркасон',
    'price': 1150,
    'category': 'Сімейні',
    'players': '2–5',
    'description': 'Гра про будівництво середньовічних міст.',
    'in_stock': True,
}


@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite')})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def product(client):
    """Товар, уже створений через API."""
    return client.post('/api/products', json=VALID_PRODUCT).get_json()
