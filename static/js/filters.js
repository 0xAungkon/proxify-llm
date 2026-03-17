import { FILTER_STORAGE_KEY, state } from './state.js';
import { parseName } from './utils.js';

let renderListFn = () => {};

export function initFilters({ renderList }) {
  renderListFn = renderList;
}

function getCheckedValues(className) {
  return Array.from(document.querySelectorAll('.' + className + ':checked')).map(el => el.value);
}

function setCheckedValues(className, values) {
  const selected = new Set(Array.isArray(values) ? values : []);
  document.querySelectorAll('.' + className).forEach(el => {
    el.checked = selected.has(el.value);
  });
}

function updateMultiFilterLabels() {
  const methodBtn = document.getElementById('filter-method-btn');
  const statusBtn = document.getElementById('filter-status-btn');
  if (methodBtn) methodBtn.textContent = state.fMethods.length ? `Method (${state.fMethods.length})` : 'Method: All';
  if (statusBtn) statusBtn.textContent = state.fStatuses.length ? `Status (${state.fStatuses.length})` : 'Status: All';
}

export function closeFilterMenus() {
  document.getElementById('filter-method-menu')?.classList.add('hidden');
  document.getElementById('filter-status-menu')?.classList.add('hidden');
}

export function toggleFilterMenu(kind, event) {
  event.stopPropagation();
  const targetId = kind === 'method' ? 'filter-method-menu' : 'filter-status-menu';
  const otherId = kind === 'method' ? 'filter-status-menu' : 'filter-method-menu';
  document.getElementById(otherId)?.classList.add('hidden');
  document.getElementById(targetId)?.classList.toggle('hidden');
}

export function hasActiveFilters() {
  return Boolean(
    state.fSearch ||
    state.fMethods.length ||
    state.fStatuses.length ||
    state.fTime ||
    state.fDateFrom ||
    state.fDateTo
  );
}

function saveFiltersToStorage() {
  const payload = {
    search: state.fSearch,
    methods: state.fMethods,
    statuses: state.fStatuses,
    time: state.fTime,
    dateFrom: state.fDateFrom,
    dateTo: state.fDateTo,
  };
  localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(payload));
}

export function restoreFiltersFromStorage() {
  try {
    const raw = localStorage.getItem(FILTER_STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);

    const searchEl = document.getElementById('sidebar-search');
    const timeEl = document.getElementById('filter-time');
    const fromEl = document.getElementById('filter-date-from');
    const toEl = document.getElementById('filter-date-to');

    if (searchEl) searchEl.value = saved.search || '';
    if (timeEl) timeEl.value = saved.time || '';
    if (fromEl) fromEl.value = saved.dateFrom || '';
    if (toEl) toEl.value = saved.dateTo || '';

    setCheckedValues('method-opt', saved.methods || []);
    setCheckedValues('status-opt', saved.statuses || []);

    onTimeRangeChange();
  } catch (_) {
    // ignore parse errors
  }
}

export function applyFilters() {
  state.fSearch = (document.getElementById('sidebar-search')?.value || '').trim().toLowerCase();
  state.fMethods = getCheckedValues('method-opt');
  state.fStatuses = getCheckedValues('status-opt');
  state.fTime = document.getElementById('filter-time')?.value || '';
  state.fDateFrom = document.getElementById('filter-date-from')?.value || '';
  state.fDateTo = document.getElementById('filter-date-to')?.value || '';

  updateMultiFilterLabels();

  const searchClearBtn = document.getElementById('search-clear-btn');
  if (searchClearBtn) searchClearBtn.classList.toggle('hidden', !state.fSearch);

  const clearBtn = document.getElementById('clear-filters-btn');
  const hasFilter = state.fMethods.length || state.fStatuses.length || state.fTime || state.fDateFrom || state.fDateTo;
  if (clearBtn) clearBtn.style.display = hasFilter ? '' : 'none';

  const now = Date.now();
  const timeMap = { '1m': 60 * 1000, '5m': 5 * 60 * 1000, '15m': 15 * 60 * 1000, '30m': 30 * 60 * 1000, '1h': 60 * 60 * 1000 };

  state.filteredFiles = state.logFiles.filter(log => {
    const apiPath = '/' + (log.relative_path.split('/').slice(0, -1).join('/') || log.relative_path);
    const { method, status } = parseName(log.file_name);
    const logTime = new Date(log.date).getTime();

    if (state.fSearch && !apiPath.toLowerCase().includes(state.fSearch)) return false;
    if (state.fMethods.length && !state.fMethods.includes(method.toUpperCase())) return false;
    if (state.fStatuses.length && !state.fStatuses.some(s => String(status).startsWith(s))) return false;

    if (state.fTime && state.fTime !== 'custom') {
      if (now - logTime > (timeMap[state.fTime] || Infinity)) return false;
    } else if (state.fTime === 'custom') {
      if (state.fDateFrom) {
        const from = new Date(state.fDateFrom).getTime();
        if (logTime < from) return false;
      }
      if (state.fDateTo) {
        const to = new Date(state.fDateTo).getTime();
        if (logTime > to) return false;
      }
    }

    return true;
  });

  saveFiltersToStorage();
  renderListFn();
}

export function onTimeRangeChange() {
  const val = document.getElementById('filter-time')?.value || '';
  const customRange = document.getElementById('custom-date-range');
  if (customRange) {
    customRange.classList.toggle('hidden', val !== 'custom');
    customRange.classList.toggle('flex', val === 'custom');
  }
  applyFilters();
}

export function clearFilters() {
  const el = id => document.getElementById(id);
  setCheckedValues('method-opt', []);
  setCheckedValues('status-opt', []);
  if (el('filter-time')) el('filter-time').value = '';
  if (el('filter-date-from')) el('filter-date-from').value = '';
  if (el('filter-date-to')) el('filter-date-to').value = '';

  const customRange = document.getElementById('custom-date-range');
  if (customRange) {
    customRange.classList.add('hidden');
    customRange.classList.remove('flex');
  }
  applyFilters();
}

export function clearSearch() {
  const input = document.getElementById('sidebar-search');
  if (input) input.value = '';
  applyFilters();
}
