import { state } from './state.js';
import { escapeHtml, fmtDate, parseName, statusCls } from './utils.js';

function kvRow(label, value, valClass) {
  return `<tr class="border-b border-[#333]">
      <td class="py-1.5 pr-4 text-[#8ab4f8] font-semibold whitespace-nowrap align-top w-40">${escapeHtml(label)}</td>
      <td class="py-1.5 break-all ${valClass || ''}">${escapeHtml(String(value ?? 'null'))}</td>
  </tr>`;
}

function jsonPre(data) {
  if (data === null || data === undefined) {
    return '<span class="text-[#777] font-mono text-[12px]">null</span>';
  }
  const s = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  return `<pre class="whitespace-pre-wrap break-words text-[#a6accd] font-mono text-[12px]">${escapeHtml(s)}</pre>`;
}

function isResponseMetadata(responseBody) {
  if (typeof responseBody !== 'object' || responseBody === null) return false;
  // Check if it has metadata fields from Ollama chat completion
  return 'done' in responseBody || 'done_reason' in responseBody || 'total_duration' in responseBody;
}

function buildResponseMetadataTable(responseBody) {
  if (!responseBody || typeof responseBody !== 'object') return '';
  if (!isResponseMetadata(responseBody)) return '';
  
  const metadataFields = ['done', 'done_reason', 'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration'];
  const rows = metadataFields
    .filter(field => field in responseBody)
    .map(field => kvRow(field, responseBody[field]))
    .join('');
  
  if (!rows) return '';
  
  return `<div class="text-[#888] text-[10px] uppercase tracking-wide mb-1 font-semibold">Response Metadata</div>
    <table class="w-full mb-5"><tbody>${rows}</tbody></table>`;
}

export function switchTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    const active = btn.dataset.tab === tab;
    btn.className = 'tab-btn flex items-center justify-center cursor-pointer pb-1 border-b-2 '
      + (active ? 'text-[#8ab4f8] border-[#8ab4f8]' : 'text-[#aaa] border-transparent hover:text-[#eee]');
  });
  if (state.currentLog) renderDetails(state.currentLog);
}

export function renderDetails(logMeta) {
  state.currentLog = logMeta;
  const panel = document.getElementById('network-details');

  let data = null;
  try { data = JSON.parse(logMeta.content || ''); } catch (_) {}

  const { method, status } = parseName(logMeta.file_name);

  if (state.activeTab === 'overview') {
    const encodedPath = logMeta.relative_path.split('/').map(encodeURIComponent).join('/');
    panel.innerHTML = `<div class="p-4 font-mono text-[12px]">
        <div class="flex items-center gap-2 mb-4 flex-wrap">
            <button onclick="actionCurl('${escapeHtml(encodedPath)}')"
                class="flex items-center gap-1 px-3 py-1 rounded text-[11px] font-semibold bg-[#2a2a2a] border border-[#444] text-[#8ab4f8] hover:bg-[#333] transition-colors">⧉ Copy cURL</button>
            <a href="/admin/logs/download/${encodedPath}" download
                class="flex items-center gap-1 px-3 py-1 rounded text-[11px] font-semibold bg-[#2a2a2a] border border-[#444] text-[#6fcf97] hover:bg-[#333] transition-colors no-underline">↓ Download</a>
            <button onclick="actionReplay('${escapeHtml(encodedPath)}')"
                class="flex items-center gap-1 px-3 py-1 rounded text-[11px] font-semibold bg-[#2a2a2a] border border-[#444] text-[#c792ea] hover:bg-[#333] transition-colors">▶ Replay</button>
            <button onclick="actionDelete('${escapeHtml(logMeta.relative_path)}', '${escapeHtml(encodedPath)}')"
                class="flex items-center gap-1 px-3 py-1 rounded text-[11px] font-semibold bg-[#2a2a2a] border border-[#4d1a1a] text-[#f28b82] hover:bg-[#3a1a1a] transition-colors ml-auto">✕ Delete</button>
        </div>
        <table class="w-full"><tbody>
            ${kvRow('Request ID', data?.request_id)}
            ${kvRow('Path', data?.path)}
            ${kvRow('Method', method)}
            <tr class="border-b border-[#333]"><td class="py-1.5 pr-4 text-[#8ab4f8] font-semibold whitespace-nowrap align-top w-40">Status Code</td><td class="py-1.5 font-bold ${statusCls(status)}">${escapeHtml(String(status))}</td></tr>
            ${kvRow('Latency', data?.latency_sec != null ? data.latency_sec + ' s' : null)}
            ${kvRow('Modified', fmtDate(logMeta.date))}
            ${kvRow('File', logMeta.file_name)}
            ${kvRow('Full Path', logMeta.full_path)}
        </tbody></table>
        <div id="replay-output" class="mt-4 hidden">
            <div class="text-[#888] text-[10px] uppercase tracking-wide mb-1 font-semibold">Replay Response</div>
            <pre id="replay-content" class="whitespace-pre-wrap break-words text-[#a6accd] bg-[#1e1e1e] border border-[#333] rounded p-3 text-[12px] max-h-64 overflow-y-auto"></pre>
        </div>
    </div>`;
    return;
  }

  if (state.activeTab === 'request') {
    panel.innerHTML = `<div class="p-4">${jsonPre(data?.request ?? null)}</div>`;
    return;
  }

  panel.innerHTML = `<div class="p-4 font-mono text-[12px]">
      <table class="w-full mb-5"><tbody>
          <tr class="border-b border-[#333]"><td class="py-1.5 pr-4 text-[#8ab4f8] font-semibold whitespace-nowrap align-top w-40">Status Code</td><td class="py-1.5 font-bold ${statusCls(status)}">${escapeHtml(String(status))}</td></tr>
          ${kvRow('Latency', data?.latency_sec != null ? data.latency_sec + ' s' : null)}
      </tbody></table>
      ${data?.assistant_response != null ? `<div class="text-[#888] text-[10px] uppercase tracking-wide mb-1 font-semibold">Assistant Response</div><pre class="whitespace-pre-wrap break-words text-[#a6accd] font-mono text-[12px] mb-5">${escapeHtml(data.assistant_response)}</pre>` : ''}
      ${buildResponseMetadataTable(data?.response_body)}
      ${data?.response_body != null && !isResponseMetadata(data.response_body) ? `<div class="text-[#888] text-[10px] uppercase tracking-wide mb-1 font-semibold">Response Body</div>${jsonPre(data.response_body)}` : ''}
  </div>`;
}

export function renderError(msg) {
  document.getElementById('network-details').innerHTML =
    `<div class="flex h-full items-center justify-center px-6 text-[#f28b82] text-center">${escapeHtml(msg)}</div>`;
}
