// ============================================================
// СТОРІНКА /api-demo — головна логіка клієнтської частини.
// Отримання списку (GET), додавання (POST), редагування (PUT)
// і видалення (DELETE) товарів через REST API.
// ============================================================
import { api, ApiError } from './api-client.js';
import { DEFAULT_LIMITS, toPayload, validateProduct } from './validation.js';
import {
    fillSelect, renderLoadError, renderProducts, renderStats,
    setApiStatus, setFieldErrors, showLoading, showMessage,
} from './ui.js';

const SEARCH_DEBOUNCE_MS = 300;

const form = document.getElementById('addForm');
const submitBtn = document.getElementById('submitBtn');
const cancelEditBtn = document.getElementById('cancelEditBtn');
const formTitle = document.getElementById('formTitle');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const sortSelect = document.getElementById('sortSelect');
const resultInfo = document.getElementById('resultInfo');
const descriptionInput = document.getElementById('description');
const descriptionCounter = document.getElementById('description-counter');
const confirmDialog = document.getElementById('confirmDialog');

// Стан сторінки. Змінюється лише через присвоєння нових об'єктів.
let state = {
    categories: [],
    limits: DEFAULT_LIMITS,
    editingId: null,
    requestNo: 0, // захист від «гонки» запитів: показуємо лише відповідь на останній
};

const currentFilters = () => ({
    search: searchInput.value.trim(),
    category: categoryFilter.value,
    sort: sortSelect.value,
});

// ------------------------------------------------------------ завантаження

/** Довідники з /api/meta: категорії, варіанти сортування, обмеження полів. */
async function loadMeta() {
    try {
        const meta = await api.meta();
        state = { ...state, categories: meta.categories, limits: meta.limits };
        const categoryOptions = meta.categories.map((name) => ({ value: name, label: name }));
        fillSelect(document.getElementById('category'), categoryOptions);
        fillSelect(categoryFilter, categoryOptions);
        fillSelect(sortSelect, meta.sort_options, { keepFirst: false });
        descriptionCounter.textContent = `0 / ${meta.limits.description_max}`;
        setApiStatus('online', 'API працює');
        return true;
    } catch (error) {
        // Повідомлення користувачу покаже loadData(), щоб не дублювати дві однакові помилки
        console.error('Помилка завантаження довідників:', error);
        setApiStatus('offline', 'API недоступне');
        return false;
    }
}

/** Завантажує список товарів з урахуванням пошуку, фільтра й сортування. */
async function loadData() {
    const requestNo = state.requestNo + 1;
    state = { ...state, requestNo };
    const filters = currentFilters();
    const filtered = Boolean(filters.search || filters.category);

    try {
        showLoading(true);
        // Статистику рахуємо по всьому каталогу, а показуємо — відфільтрований список
        const [items, all] = await Promise.all([
            api.listProducts(filters),
            filtered ? api.listProducts() : null,
        ]);
        if (requestNo !== state.requestNo) return; // прийшла застаріла відповідь

        renderProducts(items, { onEdit: startEdit, onDelete: confirmDelete }, { filtered });
        renderStats(all || items);
        resultInfo.textContent = filtered ? `Знайдено: ${items.length}` : `Усього ігор: ${items.length}`;
        setApiStatus('online', 'API працює');
    } catch (error) {
        if (requestNo !== state.requestNo) return;
        console.error('Помилка завантаження:', error);
        setApiStatus('offline', 'API недоступне');
        resultInfo.textContent = '';
        renderLoadError(error.message, loadAll);
        showMessage(`Помилка завантаження: ${error.message}`, 'error');
    } finally {
        if (requestNo === state.requestNo) showLoading(false);
    }
}

async function loadAll() {
    if (!state.categories.length) await loadMeta();
    await loadData();
}

// ------------------------------------------------------------ форма

function readForm() {
    return {
        name: form.elements.name.value,
        price: form.elements.price.value,
        category: form.elements.category.value,
        players: form.elements.players.value,
        description: form.elements.description.value,
        in_stock: form.elements.in_stock.checked,
    };
}

function resetForm() {
    form.reset();
    setFieldErrors(form, {});
    state = { ...state, editingId: null };
    formTitle.textContent = 'Додати гру';
    submitBtn.textContent = 'Додати';
    cancelEditBtn.hidden = true;
    form.closest('.form-card').classList.remove('editing');
    updateCounter();
}

function startEdit(product) {
    state = { ...state, editingId: product.id };
    form.elements.name.value = product.name;
    form.elements.price.value = product.price;
    form.elements.category.value = product.category;
    form.elements.players.value = product.players;
    form.elements.description.value = product.description;
    form.elements.in_stock.checked = product.in_stock;
    setFieldErrors(form, {});
    formTitle.textContent = `Редагування: ${product.name}`;
    submitBtn.textContent = 'Зберегти зміни';
    cancelEditBtn.hidden = false;
    form.closest('.form-card').classList.add('editing');
    updateCounter();
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    form.elements.name.focus({ preventScroll: true });
}

async function saveProduct(payload) {
    const { editingId } = state;
    submitBtn.disabled = true;
    try {
        showLoading(true);
        const saved = editingId
            ? await api.updateProduct(editingId, payload)
            : await api.createProduct(payload);
        showMessage(editingId ? `Зміни в «${saved.name}» збережено.` : `Гру «${saved.name}» успішно додано!`, 'success');
        resetForm();
        await loadData();
    } catch (error) {
        console.error('Помилка збереження:', error);
        if (error instanceof ApiError && Object.keys(error.fields).length) {
            setFieldErrors(form, error.fields); // сервер підсвітив конкретні поля
        }
        if (error instanceof ApiError && error.status === 404) {
            resetForm();
            await loadData();
        }
        showMessage(`Помилка ${editingId ? 'збереження' : 'додавання'}: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        showLoading(false);
    }
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const values = readForm();
    const errors = validateProduct(values, state.categories, state.limits);
    setFieldErrors(form, errors);
    if (Object.keys(errors).length) {
        showMessage('Виправте помилки у формі — їх підсвічено червоним.', 'error');
        return;
    }
    await saveProduct(toPayload(values));
});

// Помилку поля прибираємо, щойно користувач почав його виправляти
form.addEventListener('input', (event) => {
    const field = event.target.name;
    const holder = field && document.getElementById(`${field}-error`);
    if (holder && holder.textContent) {
        holder.textContent = '';
        event.target.removeAttribute('aria-invalid');
    }
});

function updateCounter() {
    const max = state.limits.description_max;
    const length = descriptionInput.value.length;
    descriptionCounter.textContent = `${length} / ${max}`;
    descriptionCounter.classList.toggle('over', length > max);
}

descriptionInput.addEventListener('input', updateCounter);
cancelEditBtn.addEventListener('click', resetForm);

// ------------------------------------------------------------ видалення

function confirmDelete(product) {
    document.getElementById('confirmText').textContent =
        `«${product.name}» буде видалено з каталогу. Цю дію не можна скасувати.`;
    confirmDialog.onclose = async () => {
        if (confirmDialog.returnValue === 'confirm') await removeProduct(product);
    };
    confirmDialog.showModal();
}

async function removeProduct(product) {
    try {
        showLoading(true);
        await api.deleteProduct(product.id);
        if (state.editingId === product.id) resetForm();
        showMessage(`Гру «${product.name}» видалено.`, 'success');
    } catch (error) {
        console.error('Помилка видалення:', error);
        showMessage(`Помилка видалення: ${error.message}`, 'error');
    } finally {
        showLoading(false);
        await loadData();
    }
}

// ------------------------------------------------------------ фільтри

let searchTimer;
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadData, SEARCH_DEBOUNCE_MS);
});
categoryFilter.addEventListener('change', loadData);
sortSelect.addEventListener('change', loadData);
document.getElementById('refreshBtn').addEventListener('click', loadAll);

// ------------------------------------------------------------ ініціалізація

loadAll();
