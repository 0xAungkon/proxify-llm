import { state } from './state.js';
import { buildLogUrl } from './utils.js';

let renderListFn = () => {};
let loadLogDetailsFn = async () => {};
let switchTabFn = () => {};
let reloadLogsFn = async () => {};

export function initActions({ renderList, loadLogDetails, switchTab, reloadLogs }) {
  renderListFn = renderList;
  loadLogDetailsFn = loadLogDetails;
  switchTabFn = switchTab;
  reloadLogsFn = reloadLogs;
}

export async function clearAllLogs() {
  if (!confirm('Delete ALL log files? This cannot be undone.')) return;
  try {
    const res = await fetch('/admin/logs/clear', { method: 'DELETE', credentials: 'same-origin' });
    if (res.status === 401) { window.location.href = '/app/login'; return; }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Clear failed.');

    await reloadLogsFn({ keepSelection: false });
  } catch (e) {
    alert('Clear failed: ' + (e.message || 'Unknown error'));
  }
}

export async function actionDelete(relativePath, encodedPath) {
  if (!confirm('Delete this log file?')) return;
  try {
    const res = await fetch('/admin/logs/delete/' + encodedPath, {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    if (res.status === 401) { window.location.href = '/app/login'; return; }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Delete failed.');

    await reloadLogsFn({ keepSelection: true });
  } catch (e) {
    alert('Delete failed: ' + (e.message || 'Unknown error'));
  }
}

export async function actionCurl(encodedPath) {
  try {
    const res = await fetch('/admin/logs/curl/' + encodedPath, { credentials: 'same-origin' });
    if (res.status === 401) { window.location.href = '/app/login'; return; }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to generate cURL.');
    await navigator.clipboard.writeText(data.curl);
    const btn = document.querySelector('button[onclick^="actionCurl"]');
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = '✓ Copied!';
      setTimeout(() => { btn.textContent = orig; }, 1500);
    }
  } catch (e) {
    alert('cURL copy failed: ' + (e.message || 'Unknown error'));
  }
}

export async function actionReplay(encodedPath) {
  const outputBox = document.getElementById('replay-output');
  const outputPre = document.getElementById('replay-content');
  if (!outputBox || !outputPre) return;

  outputBox.classList.remove('hidden');
  outputPre.textContent = 'Replaying...';

  try {
    const res = await fetch('/admin/logs/replay/' + encodedPath, {
      method: 'POST',
      credentials: 'same-origin',
    });
    if (res.status === 401) { window.location.href = '/app/login'; return; }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let text = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      text += decoder.decode(value, { stream: true });
      outputPre.textContent = text;
      outputPre.scrollTop = outputPre.scrollHeight;
    }

    if (!text) outputPre.textContent = '(empty response)';
  } catch (e) {
    outputPre.textContent = 'Replay failed: ' + (e.message || 'Unknown error');
  }
}

export async function copyLogJson(relativePath) {
  const res = await fetch(buildLogUrl(relativePath), { credentials: 'same-origin' });
  if (res.status === 401) { window.location.href = '/app/login'; return; }
  const data = await res.json();
  await navigator.clipboard.writeText(JSON.stringify(data.log, null, 2));
}

export async function openReplayForPath(relativePath) {
  state.activePath = relativePath;
  renderListFn();
  await loadLogDetailsFn(relativePath);
  switchTabFn('overview');
  const enc = relativePath.split('/').map(encodeURIComponent).join('/');
  setTimeout(() => actionReplay(enc), 150);
}
