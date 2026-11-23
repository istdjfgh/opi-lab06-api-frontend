"""Тести REST API: коди відповідей, валідація, пошук, фільтр, сортування."""
import pytest

from conftest import VALID_PRODUCT


def test_health_returns_ok(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


def test_meta_contains_categories_and_limits(client):
    body = client.get('/api/meta').get_json()
    assert 'Сімейні' in body['categories']
    assert body['limits']['name_min'] == 2
    assert {'value': 'newest', 'label': 'Спочатку нові'} in body['sort_options']


def test_empty_list_returns_empty_array(client):
    response = client.get('/api/products')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_product_returns_201_with_location(client):
    response = client.post('/api/products', json=VALID_PRODUCT)
    body = response.get_json()
    assert response.status_code == 201
    assert response.headers['Location'] == f'/api/products/{body["id"]}'
    assert body['name'] == 'Каркасон'
    assert body['in_stock'] is True
    assert body['created_at']


def test_created_product_appears_in_list(client, product):
    items = client.get('/api/products').get_json()
    assert [item['id'] for item in items] == [product['id']]


def test_create_trims_spaces(client):
    body = client.post('/api/products', json={**VALID_PRODUCT, 'name': '  Доббль  '}).get_json()
    assert body['name'] == 'Доббль'


@pytest.mark.parametrize('field, value', [
    ('name', ''),
    ('name', 'А'),
    ('name', 'x' * 81),
    ('price', -1),
    ('price', '100'),
    ('price', True),
    ('price', 100001),
    ('category', 'Невідома'),
    ('description', 'x' * 501),
    ('in_stock', 'так'),
])
def test_create_rejects_invalid_field(client, field, value):
    response = client.post('/api/products', json={**VALID_PRODUCT, field: value})
    body = response.get_json()
    assert response.status_code == 400
    assert field in body['fields']
    assert body['error']


def test_create_rejects_non_json_body(client):
    response = client.post('/api/products', data='не json', content_type='text/plain')
    assert response.status_code == 400
    assert 'JSON' in response.get_json()['error']


def test_get_missing_product_returns_404_json(client):
    response = client.get('/api/products/999')
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Товар не знайдено'}


def test_update_product(client, product):
    response = client.put(f'/api/products/{product["id"]}', json={**VALID_PRODUCT, 'price': 999.5})
    assert response.status_code == 200
    assert response.get_json()['price'] == 999.5


def test_update_missing_product_returns_404(client):
    assert client.put('/api/products/999', json=VALID_PRODUCT).status_code == 404


def test_update_with_invalid_data_returns_400(client, product):
    response = client.put(f'/api/products/{product["id"]}', json={**VALID_PRODUCT, 'name': ''})
    assert response.status_code == 400


def test_delete_product(client, product):
    assert client.delete(f'/api/products/{product["id"]}').status_code == 204
    assert client.get(f'/api/products/{product["id"]}').status_code == 404


def test_delete_missing_product_returns_404(client):
    assert client.delete('/api/products/999').status_code == 404


def test_search_and_category_filter(client):
    client.post('/api/products', json=VALID_PRODUCT)
    client.post('/api/products', json={**VALID_PRODUCT, 'name': 'Пандемія', 'category': 'Кооперативні',
                                       'description': 'Зупиніть епідемію разом'})

    by_search = client.get('/api/products?search=епідем').get_json()
    by_category = client.get('/api/products?category=Сімейні').get_json()

    assert [p['name'] for p in by_search] == ['Пандемія']
    assert [p['name'] for p in by_category] == ['Каркасон']


def test_sort_by_price(client):
    for name, price in [('Дешева', 100), ('Дорога', 900), ('Середня', 500)]:
        client.post('/api/products', json={**VALID_PRODUCT, 'name': name, 'price': price})

    asc = [p['price'] for p in client.get('/api/products?sort=price_asc').get_json()]
    desc = [p['price'] for p in client.get('/api/products?sort=price_desc').get_json()]

    assert asc == [100, 500, 900]
    assert desc == [900, 500, 100]


def test_unknown_sort_and_category_return_400(client):
    assert client.get('/api/products?sort=drop').status_code == 400
    assert client.get('/api/products?category=Нема').status_code == 400


def test_search_is_safe_against_sql_injection(client, product):
    response = client.get("/api/products?search=' OR 1=1 --")
    assert response.status_code == 200
    assert response.get_json() == []


def test_unknown_api_route_returns_json_404(client):
    response = client.get('/api/unknown')
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Ресурс не знайдено'}


def test_wrong_method_returns_json_405(client):
    response = client.patch('/api/products')
    assert response.status_code == 405
    assert 'error' in response.get_json()


def test_cors_header_present_for_api(client):
    origin = 'http://127.0.0.1:5500'  # наприклад, Live Server у VS Code
    response = client.get('/api/products', headers={'Origin': origin})
    assert response.headers['Access-Control-Allow-Origin'] in ('*', origin)


def test_cors_not_applied_to_html_pages(client):
    response = client.get('/', headers={'Origin': 'http://127.0.0.1:5500'})
    assert 'Access-Control-Allow-Origin' not in response.headers
