// ============================================================
// КЛІЄНТ REST API
// Усі звернення до сервера проходять через функцію request():
// тут перевіряється response.ok, обробляється тайм-аут
// і мережеві помилки перетворюються на зрозумілий текст.
// ============================================================

// Сторінку віддає той самий Flask-сервер, тому достатньо відносної адреси.
export const API_BASE = '/api';

// Скільки чекати відповіді, перш ніж вважати сервер недоступним.
const REQUEST_TIMEOUT_MS = 8000;

/**
 * Помилка запиту до API.
 * status — HTTP-код (0, якщо відповіді взагалі не було),
 * fields — помилки окремих полів форми від сервера ({name: '...'}).
 */
export class ApiError extends Error {
    constructor(message, status = 0, fields = {}) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.fields = fields;
    }
}

/** Текст помилки з тіла відповіді ({"error": "..."}) або запасний варіант за кодом. */
async function readError(response) {
    const fallback = {
        400: 'Сервер відхилив дані. Перевірте поля форми.',
        404: 'Запис не знайдено — можливо, його вже видалили.',
        405: 'Сервер не підтримує цю дію.',
        500: 'Внутрішня помилка сервера. Спробуйте пізніше.',
    }[response.status] || `HTTP помилка! Статус: ${response.status}`;

    try {
        const body = await response.json();
        return new ApiError(body.error || fallback, response.status, body.fields || {});
    } catch {
        // Тіло не JSON (наприклад, HTML-сторінка проксі) — показуємо загальний текст
        return new ApiError(fallback, response.status);
    }
}

/**
 * Виконує запит до API і повертає розібраний JSON (або null для 204 No Content).
 * fetch() відхиляє проміс лише коли сервер недоступний, тому коди 4xx/5xx
 * перевіряємо самі через response.ok.
 */
async function request(path, { method = 'GET', body } = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    const options = { method, signal: controller.signal, headers: { Accept: 'application/json' } };
    if (body !== undefined) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    let response;
    try {
        response = await fetch(API_BASE + path, options);
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new ApiError(`Сервер не відповів за ${REQUEST_TIMEOUT_MS / 1000} с. Спробуйте ще раз.`);
        }
        // TypeError: Failed to fetch — сервер зупинено або немає мережі
        throw new ApiError('Не вдалося з\'єднатися з сервером. Перевірте, чи запущено API.');
    } finally {
        clearTimeout(timer);
    }

    if (!response.ok) {
        throw await readError(response);
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
}

// ------------------------------------------------------------ ендпоінти

export const api = {
    health: () => request('/health'),
    meta: () => request('/meta'),

    /** filters: { search, category, sort } — порожні значення не передаються */
    listProducts(filters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value) params.set(key, value);
        });
        const query = params.toString();
        return request('/products' + (query ? `?${query}` : ''));
    },

    createProduct: (product) => request('/products', { method: 'POST', body: product }),
    updateProduct: (id, product) => request(`/products/${id}`, { method: 'PUT', body: product }),
    deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' }),
};
