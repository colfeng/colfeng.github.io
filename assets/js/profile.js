(() => {
  const toggle = document.querySelector('#duanyu-folio [data-theme]');
  if (!toggle) return;
  const media = matchMedia('(prefers-color-scheme: dark)');
  const current = () => document.documentElement.style.colorScheme || (media.matches ? 'dark' : 'light');
  const sync = () => toggle.setAttribute('aria-pressed', String(current() === 'dark'));
  sync();
  toggle.addEventListener('click', () => {
    const next = current() === 'dark' ? 'light' : 'dark';
    document.documentElement.style.colorScheme = next;
    try { localStorage.setItem('duanyu-theme', next); } catch (_) {}
    sync();
  });
  media.addEventListener('change', sync);
})();
