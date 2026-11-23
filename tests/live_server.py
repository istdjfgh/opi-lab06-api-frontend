"""Живий Flask-сервер у фоновому потоці — для браузерних тестів і скриншотів.

Сервер можна зупинити посеред тесту, щоб перевірити, що бачить
користувач, коли API недоступне.
"""
import os
import sys
import threading

from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
import models  # noqa: E402


class LiveServer:
    def __init__(self, database, products=()):
        self.app = create_app({'TESTING': True, 'DATABASE': database})
        with self.app.app_context():
            for product in products:
                models.create_product(product)
        self._server = make_server('127.0.0.1', 0, self.app, threaded=True)
        self.url = f'http://127.0.0.1:{self._server.server_port}'
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()


def launch_browser(playwright):
    """Вбудований Chromium Playwright, а якщо його не встановлено — системний Chrome."""
    try:
        return playwright.chromium.launch()
    except Exception:
        return playwright.chromium.launch(channel='chrome')
