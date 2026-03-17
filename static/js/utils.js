export function escapeHtml(v) {
  return String(v ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function buildLogUrl(rel) {
  return '/admin/logs/' + rel.split('/').map(encodeURIComponent).join('/');
}

export function fmtDate(v) {
  const d = new Date(v);
  return isNaN(d) ? v : d.toLocaleString();
}

export function fmtTime(v) {
  const d = new Date(v);
  return isNaN(d)
    ? v
    : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function parseName(fileName) {
  const parts = fileName.replace(/\.json$/i, '').split('_');
  return {
    method: parts[0] || '',
    status: parseInt(parts[3], 10) || parts[3] || '',
  };
}

export function methodCls(m) {
  return ({
    GET: 'bg-[#1a4d2e] text-[#6fcf97]',
    POST: 'bg-[#1a2f4d] text-[#8ab4f8]',
    PUT: 'bg-[#4d3d1a] text-[#f6c90e]',
    PATCH: 'bg-[#3d1a4d] text-[#c792ea]',
    DELETE: 'bg-[#4d1a1a] text-[#f28b82]',
  })[String(m).toUpperCase()] || 'bg-[#333] text-[#ccc]';
}

export function statusCls(code) {
  const n = parseInt(code, 10);
  if (n >= 500) return 'text-[#f28b82]';
  if (n >= 400) return 'text-[#f6c90e]';
  if (n >= 300) return 'text-[#c792ea]';
  if (n >= 200) return 'text-[#6fcf97]';
  return 'text-[#aaa]';
}
