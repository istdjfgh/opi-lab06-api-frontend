"""Браузерні (E2E) тести сторінки /api-demo через Playwright.

Перевіряють увесь ланцюжок: HTML -> JavaScript -> fetch() -> Flask API -> SQLite -> відображення.
Запуск: python -m pytest tests/test_e2e.py
"""
import pytest

playwright_api = pytest.importorskip('playwright.sync_api')

from conftest import VALID_PRODUCT  # noqa: E402
from live_server import LiveServer, launch_browser  # noqa: E402

SECOND_PRODUCT = {**VALID_PRODUCT, 'name': 'Пандемія', 'category': 'Кооперативні', 'price': 1490,
                  'description': 'Командою зупиніть епідемію.'}


@pytest.fixture
def server(tmp_path):
    live = LiveServer(str(tmp_path / 'e2e.sqlite'), [VALID_PRODUCT, SECOND_PRODUCT]).start()
    yield live
    try:
        live.stop()
    except OSError:
        pass  # сервер уже зупинено в самому тесті


@pytest.fixture
def page(server):
    with playwright_api.sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.goto(server.url + '/api-demo')
        page.wait_for_selector('.product')
        yield page
        assert errors == [], f'JavaScript-помилки на сторінці: {errors}'
        browser.close()


def card_titles(page):
    return page.locator('.product-title').all_inner_texts()


def test_list_is_loaded_from_api(page):
    assert sorted(card_titles(page)) == ['Каркасон', 'Пандемія']
    assert page.locator('#statTotal').inner_text() == '2'
    assert page.locator('#apiStatus').get_attribute('data-state') == 'online'


def test_client_validation_blocks_bad_form(page):
    page.fill('#name', 'А')
    page.fill('#price', '-5')
    page.click('#submitBtn')

    assert 'щонайменше 2' in page.locator('#name-error').inner_text()
    assert 'від 0' in page.locator('#price-error').inner_text()
    assert page.locator('#category-error').inner_text() == 'Оберіть категорію.'
    assert page.locator('#name').get_attribute('aria-invalid') == 'true'
    assert page.locator('.toast.error').count() == 1
    assert len(card_titles(page)) == 2  # нічого не відправлено


def test_add_product_shows_success_and_new_card(page):
    page.fill('#name', 'Доббль')
    page.fill('#price', '420')
    page.select_option('#category', 'Дитячі')
    page.fill('#players', '2–8')
    page.fill('#description', 'Гра на уважність')
    page.click('#submitBtn')

    page.wait_for_selector('.toast.success')
    assert 'успішно додано' in page.locator('.toast.success').inner_text()
    page.wait_for_function("document.querySelectorAll('.product').length === 3")
    assert card_titles(page)[0] == 'Доббль'  # сортування «спочатку нові»
    assert page.locator('#name').input_value() == ''  # форму очищено


def test_edit_product(page):
    page.locator('.product', has_text='Каркасон').get_by_role('button', name='Редагувати «Каркасон»').click()
    assert page.locator('#formTitle').inner_text() == 'Редагування: Каркасон'
    page.fill('#price', '999')
    page.click('#submitBtn')

    page.wait_for_selector('.toast.success')
    card = page.locator('.product', has_text='Каркасон')
    assert '999' in card.locator('.price').inner_text()
    assert page.locator('#formTitle').inner_text() == 'Додати гру'


def test_delete_product_with_confirmation(page):
    page.get_by_role('button', name='Видалити «Пандемія»').click()
    assert page.locator('#confirmDialog').is_visible()
    page.click('#confirmYes')

    page.wait_for_selector('.toast.success')
    page.wait_for_function("document.querySelectorAll('.product').length === 1")
    assert card_titles(page) == ['Каркасон']


def test_search_filters_list(page):
    page.fill('#searchInput', 'епідем')
    page.wait_for_function("document.querySelectorAll('.product').length === 1")
    assert card_titles(page) == ['Пандемія']
    assert page.locator('#resultInfo').inner_text() == 'Знайдено: 1'

    page.fill('#searchInput', 'немає такої гри')
    page.wait_for_selector('.empty-state')
    assert 'нічого не знайдено' in page.locator('.empty-state').inner_text()


def test_user_input_is_not_executed_as_html(page):
    page.fill('#name', '<img src=x onerror="window.hacked=1">')
    page.fill('#price', '100')
    page.select_option('#category', 'Вечірки')
    page.click('#submitBtn')

    page.wait_for_selector('.toast.success')
    assert page.locator('.product-title', has_text='<img').count() == 1
    assert page.evaluate('window.hacked') is None


def test_server_down_shows_clear_error(page, server):
    server.stop()
    page.click('#refreshBtn')

    page.wait_for_selector('.error-state')
    assert 'Перевірте, чи запущено API' in page.locator('.error-state').inner_text()
    assert page.locator('#apiStatus').get_attribute('data-state') == 'offline'
    assert page.locator('.toast.error').count() >= 1
