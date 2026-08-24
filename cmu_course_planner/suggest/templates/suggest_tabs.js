<script>
async function decompressRoute(encoded) {
  const binary = atob(encoded);
  const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).text();
}

function routeMessage(view, message, className = 'meta') {
  const paragraph = document.createElement('p');
  paragraph.className = className;
  paragraph.textContent = message;
  view.replaceChildren(paragraph);
}

async function showRoute(panel, button) {
  const index = Number(button.dataset.routeIndex);
  const view = panel.querySelector('.route-panel');
  const renderToken = (panel.renderToken || 0) + 1;
  panel.renderToken = renderToken;
  panel.querySelectorAll('.route-tree-leaf').forEach(item => {
    item.classList.remove('is-selected');
    item.setAttribute('aria-selected', 'false');
  });
  button.classList.add('is-selected');
  button.setAttribute('aria-selected', 'true');
  routeMessage(view, 'Loading route…');
  try {
    panel.routeHtml[index] ??= await decompressRoute(panel.routeData[index]);
    if (panel.renderToken !== renderToken) return;
    view.innerHTML = panel.routeHtml[index];
    initializeRouteContent(view);
  } catch (error) {
    if (panel.renderToken !== renderToken) return;
    routeMessage(view, `Could not load this route: ${error.message}`, 'semester-unit-warning');
  }
}

function initializeSchedulePanel(panel) {
  if (panel.routeData) return;
  panel.routeData = JSON.parse(panel.querySelector('.route-data').textContent);
  panel.routeHtml = [];
  panel.querySelectorAll('.route-tree-leaf').forEach(button => {
    button.addEventListener('click', () => showRoute(panel, button));
  });
  const firstButton = panel.querySelector('.route-tree-leaf');
  if (firstButton) showRoute(panel, firstButton);
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const panel = document.getElementById('tab-' + btn.dataset.tab);
    panel.classList.add('active');
    initializeSchedulePanel(panel);
  });
});

function initializeDetails(root) {
  root.querySelectorAll('details.prereq-info, details.semester-offerings-info').forEach(details => {
    details.addEventListener('toggle', () => {
      if (!details.open) return;
      document.querySelectorAll('details.prereq-info[open], details.semester-offerings-info[open]').forEach(other => {
        if (other !== details) other.removeAttribute('open');
      });
    });
  });
}
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

function setOptions(select, options, value, label) {
  select.replaceChildren(...options.map(option => {
    const element = document.createElement('option');
    element.value = String(option[value]);
    element.textContent = option[label];
    return element;
  }));
}

function setSwapOptions(select, swaps) {
  select.replaceChildren(...swaps.map(swap => {
    const element = document.createElement('option');
    element.value = swap.remove;
    element.textContent = (swap.status === 'works' ? '✓ Works · ' : '✕ Rejected · ') + swap.removeLabel;
    return element;
  }));
}

function renderWhatIfResult(root, result) {
  const output = root.querySelector('.what-if-result');
  const works = result.status === 'works';
  output.className = 'what-if-result ' + (works ? 'what-if-works' : 'what-if-rejected');
  output.replaceChildren();

  const heading = document.createElement('strong');
  heading.textContent = works ? '✓ Works' : '✕ Rejected';
  const summary = document.createElement('span');
  summary.textContent = result.summary;
  output.append(heading, summary);

  result.reasons.forEach(message => {
    const detail = document.createElement('p');
    detail.textContent = message;
    output.append(detail);
  });
  result.warnings.forEach(message => {
    const warning = document.createElement('p');
    warning.className = 'what-if-warning';
    warning.textContent = message;
    output.append(warning);
  });
}

function refreshWhatIf(root, level) {
  const data = root.whatIfData;
  const courseSelect = root.querySelector('.what-if-course');
  const semesterSelect = root.querySelector('.what-if-semester');
  const swapSelect = root.querySelector('.what-if-swap');
  const course = data.courses.find(item => item.id === courseSelect.value) || data.courses[0];
  if (!course) return;

  if (level === 'course') {
    setOptions(semesterSelect, course.semesters, 'index', 'label');
    const firstOffered = course.semesters.find(item => item.offered);
    if (firstOffered) semesterSelect.value = String(firstOffered.index);
  }
  const semester = course.semesters.find(item => String(item.index) === semesterSelect.value) || course.semesters[0];
  if (level !== 'swap') {
    setSwapOptions(swapSelect, semester.swaps);
  }
  const result = semester.swaps.find(item => item.remove === swapSelect.value) || semester.swaps[0];
  renderWhatIfResult(root, result);
}

function initializeWhatIf(root) {
  root.whatIfData = JSON.parse(root.querySelector('.what-if-data').textContent);
  root.querySelector('.what-if-course').addEventListener('change', () => refreshWhatIf(root, 'course'));
  root.querySelector('.what-if-semester').addEventListener('change', () => refreshWhatIf(root, 'semester'));
  root.querySelector('.what-if-swap').addEventListener('change', () => refreshWhatIf(root, 'swap'));
  refreshWhatIf(root, 'course');
}

function initializeRouteContent(root) {
  initializeDetails(root);
  root.querySelectorAll('.what-if').forEach(initializeWhatIf);
  root.querySelectorAll('.what-if-open').forEach(button => {
    button.addEventListener('click', () => {
      const panel = root.querySelector(`#${CSS.escape(button.dataset.whatIfTarget)}`);
      panel.querySelector('.what-if-course').value = button.dataset.course;
      refreshWhatIf(panel, 'course');
      panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      panel.querySelector('.what-if-semester').focus({ preventScroll: true });
    });
  });
}

const initialPanel = document.querySelector('.tab-panel.active');
if (initialPanel) initializeSchedulePanel(initialPanel);
</script>
