import { state } from './state.js';
import { buildLogUrl } from './utils.js';
import { renderDetails, renderError, switchTab } from './details.js';
import { initSidebar, renderList, toggleSidebarView } from './sidebar.js';
import { applyFilters, clearFilters, clearSearch, closeFilterMenus, hasActiveFilters, initFilters, onTimeRangeChange, restoreFiltersFromStorage, toggleFilterMenu } from './filters.js';
import { actionCurl, actionDelete, actionReplay, clearAllLogs, copyLogJson, initActions, openReplayForPath } from './actions.js';
import { initContextMenu, showCtxMenu } from './contextMenu.js';
import { initSidebarResize } from './resize.js';
import { toggleTheme, initTheme } from './theme.js';
import { handleLogout } from './auth.js';

const AUTO_REFRESH_SECONDS = 10;
let refreshCountdown = AUTO_REFRESH_SECONDS;
let refreshTimerId = null;
let isReloadingLogs = false;

async function loadLogDetails(relativePath) {
  try {
    const res = await fetch(buildLogUrl(relativePath), { credentials: 'same-origin' });
    if (res.status === 401) { window.location.href = '/app/login'; return; }

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Unable to load log details.');

    renderDetails(data.log);
  } catch (e) {
    renderError(e.message || 'Unable to load log details.');
  }
}

function updateRefreshCounter() {
  const el = document.getElementById('refresh-countdown');
  if (el) el.textContent = String(refreshCountdown);
}

function resetRefreshCounter() {
  refreshCountdown = AUTO_REFRESH_SECONDS;
  updateRefreshCounter();
}

function startAutoRefresh() {
  if (refreshTimerId) clearInterval(refreshTimerId);
  resetRefreshCounter();
  refreshTimerId = setInterval(async () => {
    refreshCountdown -= 1;
    if (refreshCountdown <= 0) {
      await reloadLogs({ keepSelection: true });
      return;
    }
    updateRefreshCounter();
  }, 1000);
}

async function reloadLogs({ keepSelection = true } = {}) {
  if (isReloadingLogs) return;
  isReloadingLogs = true;
  try {
    const res = await fetch('/admin/logs', { credentials: 'same-origin' });
    if (res.status === 401) { window.location.href = '/app/login'; return; }

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Unable to load logs.');

    const previousActivePath = keepSelection ? state.activePath : null;
    state.logFiles = (data.logs || []).sort((a, b) => new Date(b.date) - new Date(a.date));
    document.getElementById('log-count').textContent = state.logFiles.length + ' logs';
    applyFilters();

    const source = state.filteredFiles.length || hasActiveFilters() ? state.filteredFiles : state.logFiles;
    if (source.length > 0) {
      const stillExists = previousActivePath && source.some(l => l.relative_path === previousActivePath);
      state.activePath = stillExists ? previousActivePath : source[0].relative_path;
      renderList();
      await loadLogDetails(state.activePath);
    } else {
      state.activePath = null;
      renderError(state.logFiles.length ? 'No log files match current filters.' : 'No log files found.');
    }
    resetRefreshCounter();
  } catch (e) {
    renderError(e.message || 'Unable to load logs.');
  } finally {
    isReloadingLogs = false;
  }
}

function bindGlobals() {
  window.applyFilters = applyFilters;
  window.onTimeRangeChange = onTimeRangeChange;
  window.clearFilters = clearFilters;
  window.clearSearch = clearSearch;
  window.clearAllLogs = clearAllLogs;
  window.switchTab = switchTab;
  window.toggleSidebarView = toggleSidebarView;
  window.toggleFilterMenu = toggleFilterMenu;
  window.actionCurl = actionCurl;
  window.actionDelete = actionDelete;
  window.actionReplay = actionReplay;
  window.toggleTheme = toggleTheme;
  window.handleLogout = handleLogout;
}

function restoreSidebarViewFromStorage() {
  const saved = localStorage.getItem('proxify_sidebar_view');
  if (saved && (saved === 'list' || saved === 'tree')) {
    state.sidebarView = saved;
  }
}

function init() {
  bindGlobals();

  initTheme();
  restoreSidebarViewFromStorage();
  initFilters({ renderList });
  initSidebar({
    onSelectLog: async relativePath => {
      state.activePath = relativePath;
      renderList();
      await loadLogDetails(relativePath);
    },
    onContextMenu: (log, x, y) => showCtxMenu(x, y, log),
  });

  initActions({ renderList, loadLogDetails, switchTab, reloadLogs });

  initContextMenu({
    onView: async rel => {
      state.activePath = rel;
      renderList();
      await loadLogDetails(rel);
    },
    onCurl: async enc => actionCurl(enc),
    onCopy: async rel => copyLogJson(rel),
    onDownload: (enc, fileName) => {
      const a = document.createElement('a');
      a.href = '/admin/logs/download/' + enc;
      a.download = fileName;
      a.click();
    },
    onReplay: async rel => openReplayForPath(rel),
    onDelete: async (rel, enc) => actionDelete(rel, enc),
  });

  initSidebarResize();

  document.addEventListener('click', e => {
    if (!e.target.closest('#filter-method-wrap') && !e.target.closest('#filter-status-wrap')) {
      closeFilterMenus();
    }
  });

  document.getElementById('refresh-now-btn')?.addEventListener('click', async () => {
    await reloadLogs({ keepSelection: true });
  });

  restoreFiltersFromStorage();
  reloadLogs({ keepSelection: false });
  startAutoRefresh();

  document.addEventListener('DOMContentLoaded', () => window.lucide?.createIcons?.());
  if (document.readyState !== 'loading') window.lucide?.createIcons?.();
}

init();
