import { state } from './state.js';
import { escapeHtml, fmtTime, methodCls, parseName, statusCls } from './utils.js';
import { hasActiveFilters } from './filters.js';

let onSelect = async () => {};
let onContext = () => {};
const expandedFolders = new Set();

export function initSidebar({ onSelectLog, onContextMenu }) {
  onSelect = onSelectLog;
  onContext = onContextMenu;
  updateViewToggleButton();
}

function getSource() {
  return state.filteredFiles.length || hasActiveFilters() ? state.filteredFiles : state.logFiles;
}

function apiPathFromLog(log) {
  return '/' + (log.relative_path.split('/').slice(0, -1).join('/') || log.relative_path);
}

function createLogRow(log, apiPath, extraClasses = '') {
  const sel = log.relative_path === state.activePath;
  const { method, status } = parseName(log.file_name);

  const row = document.createElement('div');
  row.className = 'flex items-center gap-2 px-2 py-[5px] cursor-pointer border-b border-[#2c2c2c] text-[12px] '
    + (sel ? 'bg-[#1a3a5c]' : 'hover:bg-[#2a2a2a]') + (extraClasses ? ` ${extraClasses}` : '');

  row.onclick = () => onSelect(log.relative_path);
  row.addEventListener('contextmenu', e => {
    e.preventDefault();
    onContext(log, e.clientX, e.clientY);
  });

  row.innerHTML =
    `<span class="inline-block text-[10px] font-bold px-1 py-px rounded flex-shrink-0 w-14 text-center truncate ${methodCls(method)}">${escapeHtml(method)}</span>`
    + `<span class="flex-1 truncate text-[#cccccc]" title="${escapeHtml(apiPath)}">${escapeHtml(apiPath)}</span>`
    + `<span class="flex-shrink-0 font-mono font-semibold ${statusCls(status)}">${escapeHtml(String(status))}</span>`
    + `<span class="flex-shrink-0 text-[11px] text-[#888] w-[6.5rem] text-right" title="${escapeHtml(log.date)}">${escapeHtml(fmtTime(log.date))}</span>`;

  return row;
}

function buildPathTree(source) {
  const root = { children: new Map(), logs: [] };

  source.forEach(log => {
    const path = apiPathFromLog(log).replace(/^\/+/, '');
    const segments = path ? path.split('/') : ['root'];
    let node = root;
    let currentPath = '';

    segments.forEach(seg => {
      currentPath = currentPath ? `${currentPath}/${seg}` : seg;
      if (!node.children.has(seg)) {
        node.children.set(seg, { name: seg, key: currentPath, children: new Map(), logs: [] });
      }
      node = node.children.get(seg);
    });

    node.logs.push(log);
  });

  return root;
}

function renderTreeNode(container, node, depth = 0) {
  const childNodes = Array.from(node.children.values()).sort((a, b) => a.name.localeCompare(b.name));

  childNodes.forEach(child => {
    const hasChildren = child.children.size > 0 || child.logs.length > 0;
    const expanded = expandedFolders.has(child.key);

    const folderRow = document.createElement('div');
    folderRow.className = 'flex items-center gap-1 px-2 py-[4px] border-b border-[#2c2c2c] text-[12px] cursor-pointer hover:bg-[#2a2a2a] text-[#b9c1cc]';
    folderRow.style.paddingLeft = `${8 + depth * 14}px`;
    folderRow.innerHTML = `<i data-lucide="${hasChildren ? (expanded ? 'chevron-down' : 'chevron-right') : 'dot'}" class="w-3 h-3 text-[#b9c1cc] inline-block flex-shrink-0"></i><span class="truncate">${escapeHtml(child.name)}</span>`;
    folderRow.onclick = () => {
      if (!hasChildren) return;
      if (expandedFolders.has(child.key)) expandedFolders.delete(child.key);
      else expandedFolders.add(child.key);
      renderList();
    };
    container.appendChild(folderRow);

    if (!expanded) return;

    child.logs
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .forEach(log => {
        const row = createLogRow(log, apiPathFromLog(log), 'border-b-[#1f1f1f]');
        row.style.paddingLeft = `${24 + depth * 14}px`;
        container.appendChild(row);
      });

    renderTreeNode(container, child, depth + 1);
  });
}

function updateViewToggleButton() {
  const btn = document.getElementById('sidebar-view-toggle');
  if (!btn) return;
  const isList = state.sidebarView === 'list';
  btn.textContent = isList ? 'Tree' : 'List';
  btn.title = isList ? 'Switch to Tree view' : 'Switch to List view';
}

export function toggleSidebarView() {
  state.sidebarView = state.sidebarView === 'list' ? 'tree' : 'list';
  localStorage.setItem('proxify_sidebar_view', state.sidebarView);
  updateViewToggleButton();
  renderList();
}

export function renderList() {
  const container = document.getElementById('network-list');
  if (!container) return;
  container.innerHTML = '';

  const source = getSource();

  if (!source.length) {
    container.innerHTML = '<div class="px-3 py-3 text-[#777]">'
      + (state.logFiles.length ? 'No results match the current filters.' : 'No log files available.')
      + '</div>';
    return;
  }

  if (state.sidebarView === 'tree') {
    const tree = buildPathTree(source);
    renderTreeNode(container, tree, 0);
  } else {
    source.forEach(log => {
      container.appendChild(createLogRow(log, apiPathFromLog(log)));
    });
  }

  // Initialize any Lucide icons added to the DOM
  if (window.lucide) {
    window.lucide.createIcons();
  }
}
