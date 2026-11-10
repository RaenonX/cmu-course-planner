<script>
function initializeRouteFilters(panel) {
  const selectors = [...panel.querySelectorAll('.route-course-options select')];
  const clear = panel.querySelector('.clear-route-courses');
  const masks = new Map(degreePaths.courses.map(course => [course.id, course.mask]));
  function applyFilters() {
    let required = 0n;
    let excluded = 0n;
    selectors.forEach(select => {
      select.dataset.preference = select.value;
      if (select.value === 'required') required |= masks.get(select.dataset.course);
      if (select.value === 'excluded') excluded |= masks.get(select.dataset.course);
    });
    clear.disabled = !(required || excluded);
    renderPathTree(panel, required, excluded).catch(error => {
      routeMessage(panel.querySelector('.route-panel'), error.message, 'semester-unit-warning');
    });
  }
  selectors.forEach(select => select.addEventListener('change', applyFilters));
  clear.addEventListener('click', () => {
    selectors.forEach(select => { select.value = 'optional'; });
    applyFilters();
  });
  applyFilters();
}
</script>
