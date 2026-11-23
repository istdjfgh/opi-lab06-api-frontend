// ============================================================
// ВАЛІДАЦІЯ ФОРМИ У БРАУЗЕРІ
// Обмеження (limits) приходять з GET /api/meta — ті самі, що
// перевіряє сервер у validation.py. Сервер усе одно перевіряє
// дані повторно: клієнтській перевірці довіряти не можна.
// ============================================================

/** Значення за замовчуванням, якщо /api/meta ще не завантажилось. */
export const DEFAULT_LIMITS = {
    name_min: 2,
    name_max: 80,
    price_min: 0,
    price_max: 100000,
    players_max: 20,
    description_max: 500,
};

/**
 * Перевіряє значення форми.
 * values: { name, price (рядок з поля), category, players, description }
 * Повертає об'єкт помилок { поле: текст }; порожній об'єкт — помилок немає.
 */
export function validateProduct(values, categories, limits = DEFAULT_LIMITS) {
    const errors = {};
    const name = values.name.trim();
    const priceText = values.price.trim().replace(',', '.');
    const price = Number(priceText);

    if (!name) {
        errors.name = 'Вкажіть назву гри.';
    } else if (name.length < limits.name_min) {
        errors.name = `Назва має містити щонайменше ${limits.name_min} символи.`;
    } else if (name.length > limits.name_max) {
        errors.name = `Назва може містити не більше ${limits.name_max} символів.`;
    }

    if (!priceText) {
        errors.price = 'Вкажіть ціну.';
    } else if (!Number.isFinite(price)) {
        errors.price = 'Ціна має бути числом, наприклад 990 або 449.50.';
    } else if (price < limits.price_min || price > limits.price_max) {
        errors.price = `Ціна має бути від ${limits.price_min} до ${limits.price_max} грн.`;
    }

    if (!values.category) {
        errors.category = 'Оберіть категорію.';
    } else if (categories.length && !categories.includes(values.category)) {
        errors.category = 'Оберіть категорію зі списку.';
    }

    if (values.players.trim().length > limits.players_max) {
        errors.players = `Не більше ${limits.players_max} символів.`;
    }

    if (values.description.trim().length > limits.description_max) {
        errors.description = `Опис може містити не більше ${limits.description_max} символів.`;
    }

    return errors;
}

/** Перетворює значення форми на об'єкт для JSON (ціна — число, текст без зайвих пробілів). */
export function toPayload(values) {
    return {
        name: values.name.trim(),
        price: Number(values.price.trim().replace(',', '.')),
        category: values.category,
        players: values.players.trim(),
        description: values.description.trim(),
        in_stock: values.in_stock,
    };
}
