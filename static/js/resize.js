export function initSidebarResize() {
  const resizer = document.getElementById('sidebar-resizer');
  const panel = document.getElementById('sidebar-panel');
  if (!resizer || !panel) return;

  let dragging = false;

  resizer.addEventListener('mousedown', e => {
    dragging = true;
    resizer.classList.add('active');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });

  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const left = panel.parentElement.getBoundingClientRect().left;
    const newW = e.clientX - left;
    const min = 180;
    const max = panel.parentElement.offsetWidth * 0.75;
    panel.style.width = Math.min(Math.max(newW, min), max) + 'px';
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    resizer.classList.remove('active');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  });
}
