// ============================================================
// ВІДОБРАЖЕННЯ: повідомлення, індикатор завантаження, картки товарів.
// Дані від користувача вставляються лише через textContent —
// HTML-код, введений у форму, ніколи не виконається на сторінці (захист від XSS).
// ============================================================

const MESSAGE_TIMEOUT_MS = 5000;
const priceFormat = new Intl.NumberFormat('uk-UA', { style: 'currency', currency: 'UAH', maximumFractionDigits: 2 });

export const formatPrice = (value) => priceFormat.format(value);

/** Створює елемент з класом і текстом (текст — завжди через textContent). */
function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

// ------------------------------------------------------------ повідомлення

/**
 * Показує спливне повідомлення.
 * type: 'success' | 'error' | 'info'. Зникає через 5 с або після натискання ✕.
 */
export function showMessage(text, type = 'info') {
    const region = document.getElementById('message');
    const toast = el('div', `toast ${type}`);
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = { success: '✅', error: '❌', info: 'ℹ️' }[type] || 'ℹ️';
    const close = el('button', 'toast-close', '✕');
    close.type = 'button';
    close.setAttribute('aria-label', 'Закрити повідомлення');

    toast.append(el('span', 'toast-icon', icon), el('span', 'toast-text', text), close);
    region.append(toast);
    requestAnimationFrame(() => toast.classList.add('show'));

    const remove = () => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 250);
    };
    close.addEventListener('click', remove);
    setTimeout(remove, MESSAGE_TIMEOUT_MS);
}

export function showLoading(show) {
    document.getElementById('loading').classList.toggle('show', show);
    document.getElementById('dataList').setAttribute('aria-busy', String(show));
}

export function setApiStatus(state, text) {
    const status = document.getElementById('apiStatus');
    status.dataset.state = state; // online | offline | checking
    status.querySelector('.api-status-text').textContent = text;
}

// ------------------------------------------------------------ помилки полів

export function setFieldErrors(form, errors) {
    form.querySelectorAll('.field-error').forEach((node) => { node.textContent = ''; });
    form.querySelectorAll('[aria-invalid]').forEach((node) => node.removeAttribute('aria-invalid'));

    Object.entries(errors).forEach(([field, text]) => {
        const input = form.elements.namedItem(field);
        const holder = document.getElementById(`${field}-error`);
        if (input) input.setAttribute('aria-invalid', 'true');
        if (holder) holder.textContent = text;
    });

    const first = Object.keys(errors).map((field) => form.elements.namedItem(field)).find(Boolean);
    if (first) first.focus();
}

// ------------------------------------------------------------ список товарів

function productCard(product, { onEdit, onDelete }) {
    const card = el('article', 'product');
    card.dataset.id = product.id;

    const head = el('div', 'product-head');
    head.append(
        el('span', 'badge', product.category),
        el('span', `stock ${product.in_stock ? 'in' : 'out'}`, product.in_stock ? 'В наявності' : 'Немає'),
    );

    const title = el('h3', 'product-title', product.name || 'Без назви');
    const description = el('p', 'product-desc', product.description || 'Опис ще не додано.');

    const meta = el('div', 'product-meta');
    meta.append(el('span', 'price', formatPrice(product.price)));
    if (product.players) meta.append(el('span', 'players', `👥 ${product.players}`));

    const actions = el('div', 'product-actions');
    const editBtn = el('button', 'btn btn-small btn-ghost', '✏️ Редагувати');
    const deleteBtn = el('button', 'btn btn-small btn-danger-ghost', '🗑 Видалити');
    editBtn.type = 'button';
    deleteBtn.type = 'button';
    editBtn.setAttribute('aria-label', `Редагувати «${product.name}»`);
    deleteBtn.setAttribute('aria-label', `Видалити «${product.name}»`);
    editBtn.addEventListener('click', () => onEdit(product));
    deleteBtn.addEventListener('click', () => onDelete(product));
    actions.append(editBtn, deleteBtn);

    card.append(head, title, description, meta, actions);
    return card;
}

/** Показує список товарів або «порожній стан», якщо їх немає. */
export function renderProducts(items, handlers, { filtered = false } = {}) {
    const container = document.getElementById('dataList');
    container.replaceChildren();

    if (!items || items.length === 0) {
        const empty = el('div', 'empty-state');
        empty.append(
            el('p', 'empty-icon', filtered ? '🔍' : '📭'),
            el('p', null, filtered
                ? 'За вашим запитом нічого не знайдено. Змініть пошук або фільтр.'
                : 'Даних поки немає. Додайте першу гру через форму!'),
        );
        container.append(empty);
        return;
    }
    container.append(...items.map((product) => productCard(product, handlers)));
}

/** Стан помилки замість списку — з кнопкою повторної спроби. */
export function renderLoadError(message, onRetry) {
    const container = document.getElementById('dataList');
    const box = el('div', 'error-state');
    const retry = el('button', 'btn btn-primary', '↻ Спробувати знову');
    retry.type = 'button';
    retry.addEventListener('click', onRetry);
    box.append(el('p', 'empty-icon', '⚠️'), el('p', 'error-title', 'Не вдалося завантажити каталог'),
        el('p', null, message), retry);
    container.replaceChildren(box);
}

export function renderStats(items) {
    const total = items.length;
    const inStock = items.filter((p) => p.in_stock).length;
    const avg = total ? items.reduce((sum, p) => sum + p.price, 0) / total : 0;
    document.getElementById('statTotal').textContent = String(total);
    document.getElementById('statInStock').textContent = String(inStock);
    document.getElementById('statAvg').textContent = total ? formatPrice(avg) : '—';
}

export function fillSelect(select, options, { keepFirst = true } = {}) {
    const first = keepFirst ? select.options[0] : null;
    select.replaceChildren(...(first ? [first] : []));
    options.forEach(({ value, label }) => select.append(new Option(label, value)));
}
