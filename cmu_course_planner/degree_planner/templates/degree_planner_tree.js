<script>
function routeChoices(groups, variant, ordinal) {
  const selected = Array(groups.length);
  for (let index = groups.length - 1; index >= 0; index--) {
    const choices = groups[index].choices[variant];
    selected[index] = choices[Number(ordinal % BigInt(choices.length))];
    ordinal /= BigInt(choices.length);
  }
  return selected;
}

function addRouteSummary(button, used) {
  const ratings = new Map();
  const categories = new Map();
  for (const course of degreePaths.courses) {
    if (!(course.mask & used)) continue;
    ratings.set(course.rating, (ratings.get(course.rating) || 0) + 1);
    course.categories.forEach(category => categories.set(category, (categories.get(category) || 0) + 1));
  }
  const summary = document.createElement('span');
  summary.className = 'route-count-summary';
  for (const [rating, count] of [...ratings].sort((a, b) => b[0] - a[0])) {
    const badge = document.createElement('span');
    badge.className = 'tag tag-rating';
    badge.title = `${rating}/5`;
    badge.textContent = `★${rating}: ${count}`;
    summary.append(badge);
  }
  for (const [category, count] of [...categories].sort()) {
    const badge = document.createElement('span');
    badge.className = `tag ${category === 'Quant' ? 'tag-quant' : 'tag-hft'}`;
    badge.textContent = `${category}: ${count}`;
    summary.append(badge);
  }
  button.append(summary);
}

function renderRouteLeaves(panel, container, groups, used, total, autoSelect, offset) {
  const variant = Number(panel.dataset.variant);
  let start = 0n;
  const pageSize = 100n;
  function render() {
    container.replaceChildren();
    const end = start + pageSize < total ? start + pageSize : total;
    for (let ordinal = start; ordinal < end; ordinal++) {
      const choices = routeChoices(groups, variant, ordinal);
      const button = document.createElement('button');
      button.className = 'route-tree-leaf';
      button.setAttribute('role', 'treeitem');
      button.setAttribute('aria-selected', 'false');
      const title = document.createElement('span');
      title.className = 'route-tree-route';
      title.textContent = `Route ${offset + ordinal + 1n}`;
      const sections = document.createElement('span');
      sections.className = 'route-section-choice';
      sections.textContent = choices.map((choice, index) => degreePaths.terms[index].labels[choice])
        .filter(Boolean).join(' · ') || 'No elective sections';
      button.append(title, sections);
      addRouteSummary(button, used);
      button.addEventListener('click', () => showRoute(panel, button, choices, used));
      container.append(button);
      if (autoSelect && ordinal === 0n) showRoute(panel, button, choices, used);
    }
    if (total > pageSize) {
      const controls = document.createElement('div');
      const label = document.createElement('span');
      label.textContent = `${(start + 1n).toLocaleString()}–${end.toLocaleString()} of ${total.toLocaleString()} routes `;
      controls.append(label);
      for (const [text, next, disabled] of [
        ['Previous', start - pageSize, start === 0n], ['Next', end, end === total],
      ]) {
        const button = document.createElement('button');
        button.textContent = text;
        button.disabled = disabled;
        button.addEventListener('click', () => { start = next; autoSelect = false; render(); });
        controls.append(button);
      }
      container.append(controls);
    }
  }
  render();
}

async function renderPathTree(panel, required = 0n, excluded = 0n) {
  const version = (panel.filterVersion || 0) + 1;
  panel.filterVersion = version;
  panel.renderToken = (panel.renderToken || 0) + 1;
  const result = await workerRequest('count', {required, excluded});
  if (panel.filterVersion !== version) return;
  const tree = panel.querySelector('.route-tree');
  tree.replaceChildren();
  const count = (index, used) => {
    if ((used & excluded) || (index === degreePaths.terms.length && (required & ~used))) return 0n;
    if (index === degreePaths.terms.length) return 1n;
    return result.memo.get(`${index}:${used}`) || 0n;
  };
  const total = count(0, 0n);
  panel.querySelector('.route-count').textContent = `${total} route${total === 1n ? '' : 's'}`;
  panel.renderToken = (panel.renderToken || 0) + 1;
  if (!total) {
    routeMessage(panel.querySelector('.route-panel'), 'No degree plans match the selected courses.', 'semester-unit-warning');
    return;
  }
  const variant = Number(panel.dataset.variant);
  function level(index, groups, used, factor, container, autoOpen, offset) {
    if (index === degreePaths.terms.length) {
      renderRouteLeaves(panel, container, groups, used, factor, autoOpen, offset);
      return;
    }
    const term = degreePaths.terms[index];
    let first = true;
    for (const id of term.orders[variant]) {
      const group = term.groups[id];
      if (group.mask & used) continue;
      const nextUsed = used | group.mask;
      const nextFactor = factor * BigInt(group.choices[variant].length);
      const branches = nextFactor * count(index + 1, nextUsed);
      if (!branches) continue;
      const branchOffset = offset;
      offset += branches;
      const details = document.createElement('details');
      details.className = 'route-tree-branch';
      details.setAttribute('role', 'treeitem');
      const summary = document.createElement('summary');
      const label = document.createElement('span');
      label.textContent = `Semester ${index + 1} · ${group.label}`;
      const badge = document.createElement('span');
      badge.className = 'route-tree-count';
      badge.textContent = `${branches} route${branches === 1n ? '' : 's'}`;
      summary.append(label, badge);
      const children = document.createElement('div');
      children.className = 'route-tree-children';
      children.setAttribute('role', 'group');
      let loaded = false;
      function expand(selectFirst) {
        if (loaded) return;
        loaded = true;
        level(index + 1, [...groups, group], nextUsed, nextFactor, children, selectFirst, branchOffset);
      }
      details.addEventListener('toggle', () => { if (details.open) expand(false); });
      details.append(summary, children);
      container.append(details);
      if (autoOpen && first) {
        details.open = true;
        expand(true);
      }
      first = false;
    }
  }
  level(0, [], 0n, 1n, tree, true, 0n);
}
</script>
