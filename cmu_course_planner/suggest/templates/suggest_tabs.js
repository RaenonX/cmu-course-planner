<script>
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});
document.querySelectorAll('.route-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const panel = btn.closest('.tab-panel');
    panel.querySelectorAll('.route-tab-btn').forEach(b => b.classList.remove('active'));
    panel.querySelectorAll('.route-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.routePanel).classList.add('active');
  });
});
document.querySelectorAll('details.prereq-info, details.semester-offerings-info').forEach(details => {
  details.addEventListener('toggle', () => {
    if (!details.open) return;
    document.querySelectorAll('details.prereq-info[open], details.semester-offerings-info[open]').forEach(other => {
      if (other !== details) other.removeAttribute('open');
    });
  });
});
document.addEventListener('click', event => {
  document.querySelectorAll('details.prereq-info[open], details.semester-offerings-info[open]').forEach(details => {
    if (!details.contains(event.target)) details.removeAttribute('open');
  });
});
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  document.querySelectorAll('details.prereq-info[open], details.semester-offerings-info[open]').forEach(details => {
    details.removeAttribute('open');
  });
});
</script>
