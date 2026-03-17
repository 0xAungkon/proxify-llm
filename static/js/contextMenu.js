import { state } from './state.js';

let handlers = {
  onView: async () => {},
  onCurl: async () => {},
  onCopy: async () => {},
  onDownload: () => {},
  onReplay: async () => {},
  onDelete: async () => {},
};

export function showCtxMenu(x, y, log) {
  state.ctxLog = log;
  const menu = document.getElementById('ctx-menu');
  if (!menu) return;
  menu.classList.remove('hidden');

  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const mw = 190;
  const mh = 215;

  menu.style.left = (x + mw > vw ? vw - mw - 4 : x) + 'px';
  menu.style.top = (y + mh > vh ? vh - mh - 4 : y) + 'px';
}

export function hideCtxMenu() {
  document.getElementById('ctx-menu')?.classList.add('hidden');
  state.ctxLog = null;
}

export function initContextMenu(customHandlers) {
  handlers = { ...handlers, ...customHandlers };

  document.addEventListener('click', hideCtxMenu);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') hideCtxMenu();
  });

  document.addEventListener('DOMContentLoaded', () => {
    const menu = document.getElementById('ctx-menu');
    if (!menu) return;

    menu.addEventListener('click', async e => {
      e.stopPropagation();
      const item = e.target.closest('.ctx-item');
      if (!item || !state.ctxLog) return;

      const action = item.dataset.action;
      const rel = state.ctxLog.relative_path;
      const enc = rel.split('/').map(encodeURIComponent).join('/');
      const fileName = state.ctxLog.file_name;

      hideCtxMenu();

      if (action === 'view') await handlers.onView(rel);
      else if (action === 'curl') await handlers.onCurl(enc);
      else if (action === 'copy') await handlers.onCopy(rel);
      else if (action === 'download') handlers.onDownload(enc, fileName);
      else if (action === 'replay') await handlers.onReplay(rel, enc);
      else if (action === 'delete') await handlers.onDelete(rel, enc);
    });
  });
}
