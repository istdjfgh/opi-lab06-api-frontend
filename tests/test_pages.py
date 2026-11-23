"""Тести HTML-сторінок: маршрути працюють, на /api-demo є всі потрібні елементи."""


def test_pages_render(client):
    for path in ('/', '/api-demo', '/about'):
        assert client.get(path).status_code == 200


def test_api_demo_contains_required_elements(client):
    html = client.get('/api-demo').get_data(as_text=True)
    for element_id in ('message', 'loading', 'addForm', 'dataList', 'searchInput', 'confirmDialog'):
        assert f'id="{element_id}"' in html
    assert 'js/api-demo.js' in html


def test_unknown_page_returns_html_404(client):
    response = client.get('/no-such-page')
    assert response.status_code == 404
    assert 'Сторінку не знайдено' in response.get_data(as_text=True)


def test_static_files_served(client):
    for path in ('/static/js/api-demo.js', '/static/js/api-client.js', '/static/css/style.css'):
        assert client.get(path).status_code == 200
