<script>
function initializeRouteFilters(panel) {
  const selectors = [...panel.querySelectorAll('.route-course-options select')];
  const clear = panel.querySelector('.clear-route-courses');
  const leaves = [...panel.querySelectorAll('.route-tree-leaf')];
  const courses = new Map(leaves.map(leaf => [leaf, new Set(leaf.dataset.courses.split(' '))]));
  const branches = [...panel.querySelectorAll('.route-tree-branch')];

  function applyFilters() {
    selectors.forEach(select => { select.dataset.preference = select.value; });
    const selected = selectors.filter(select => select.value !== 'optional');
    clear.disabled = selected.length === 0;
    leaves.forEach(leaf => {
      leaf.hidden = !selected.every(select => select.value === 'required'
        ? courses.get(leaf).has(select.dataset.course)
        : !courses.get(leaf).has(select.dataset.course));
    });
    branches.forEach(branch => {
      const count = branch.querySelectorAll('.route-tree-leaf:not([hidden])').length;
      branch.hidden = count === 0;
      branch.querySelector('.route-tree-count').textContent = `${count} route${count === 1 ? '' : 's'}`;
    });
    const current = leaves.find(leaf => leaf.classList.contains('is-selected') && !leaf.hidden);
    const next = current || leaves.find(leaf => !leaf.hidden);
    if (next) {
      for (let parent = next.parentElement; parent && parent !== panel; parent = parent.parentElement) {
        if (parent.matches('details')) parent.open = true;
      }
      if (!current) showRoute(panel, next);
    } else {
      panel.renderToken = (panel.renderToken || 0) + 1;
      leaves.forEach(leaf => {
        leaf.classList.remove('is-selected');
        leaf.setAttribute('aria-selected', 'false');
      });
      routeMessage(panel.querySelector('.route-panel'),
        'No degree plans match the selected courses.', 'semester-unit-warning');
    }
  }

  selectors.forEach(select => select.addEventListener('change', applyFilters));
  clear.addEventListener('click', () => {
    selectors.forEach(select => { select.value = 'optional'; });
    applyFilters();
  });
  selectors.forEach(select => { select.dataset.preference = select.value; });
}
</script>
