"""Знімає скриншоти для звіту (README) у docs/screenshots.

Запуск:  python scripts/make_screenshots.py
Сервер запускається з тимчасовою базою, тож ваша db.sqlite не змінюється.
"""
import os
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))

from live_server import LiveServer, launch_browser  # noqa: E402
from seed_data import PRODUCTS  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'screenshots')
DESKTOP = {'width': 1440, 'height': 1000}
MOBILE = {'width': 390, 'height': 844}


def shot(page, name, full_page=False):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=full_page)
    print('✓', os.path.relpath(path, ROOT))


def fill_form(page, name, price, category, players='', description=''):
    page.fill('#name', name)
    page.fill('#price', price)
    if category:
        page.select_option('#category', category)
    page.fill('#players', players)
    page.fill('#description', description)


def main():
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        server = LiveServer(os.path.join(tmp, 'shots.sqlite'), PRODUCTS).start()
        with sync_playwright() as p:
            browser = launch_browser(p)
            page = browser.new_page(viewport=DESKTOP, device_scale_factor=1)

            page.goto(server.url + '/')
            shot(page, '00-home.png')

            page.goto(server.url + '/api-demo')
            page.wait_for_selector('.product')
            page.wait_for_timeout(400)
            shot(page, '01-list.png')

            # Валідація форми: помилки біля полів
            fill_form(page, 'А', '-10', '')
            page.click('#submitBtn')
            page.wait_for_timeout(350)
            shot(page, '02-validation-error.png')
            page.wait_for_function("document.querySelectorAll('.toast').length === 0", timeout=8000)

            # Додавання запису і повідомлення про успіх
            fill_form(page, 'Азул', '1290', 'Сімейні', '2–4',
                      'Викладайте візерунки з керамічних плиток для королівського палацу.')
            shot(page, '03-add-form.png')
            page.click('#submitBtn')
            page.wait_for_selector('.toast.success')
            page.wait_for_timeout(400)
            shot(page, '04-add-success.png')
            page.wait_for_function("document.querySelectorAll('.toast').length === 0", timeout=8000)

            # Редагування
            page.get_by_role('button', name='Редагувати «Пандемія»').click()
            page.fill('#price', '1390')
            page.wait_for_timeout(300)
            shot(page, '05-edit.png')
            page.click('#submitBtn')
            page.wait_for_selector('.toast.success')
            page.wait_for_function("document.querySelectorAll('.toast').length === 0", timeout=8000)

            # Пошук і фільтр
            page.select_option('#categoryFilter', 'Сімейні')
            page.wait_for_function("document.querySelector('#resultInfo').textContent.startsWith('Знайдено')")
            page.wait_for_timeout(300)
            shot(page, '06-filter.png')
            page.select_option('#categoryFilter', '')
            page.wait_for_function("document.querySelector('#resultInfo').textContent.startsWith('Усього')")

            # Підтвердження видалення
            page.get_by_role('button', name='Видалити «Доббль»').click()
            page.wait_for_timeout(250)
            shot(page, '07-delete-confirm.png')
            page.click('#confirmYes')
            page.wait_for_selector('.toast.success')
            page.wait_for_function("document.querySelectorAll('.toast').length === 0", timeout=8000)

            # Помилка від сервера (400): сервер перевіряє дані повторно
            server_error = page.evaluate(
                "fetch('/api/products', {method: 'POST', headers: {'Content-Type': 'application/json'},"
                " body: JSON.stringify({name: '', price: 'abc'})}).then(r => r.json())")
            print('  відповідь сервера на некоректні дані:', server_error)

            # Мобільна версія
            mobile = browser.new_page(viewport=MOBILE, device_scale_factor=2)
            mobile.goto(server.url + '/api-demo')
            mobile.wait_for_selector('.product')
            mobile.wait_for_timeout(300)
            shot(mobile, '08-mobile.png')
            mobile.close()

            # Сервер зупинено -> зрозуміле повідомлення про помилку
            server.stop()
            page.click('#refreshBtn')
            page.wait_for_selector('.error-state')
            page.wait_for_timeout(400)
            shot(page, '09-server-down.png')

            browser.close()


if __name__ == '__main__':
    main()
