<script>
function formatMinutes(minutes) {
  const hour = Math.floor(minutes / 60);
  return `${hour % 12 || 12}:${String(minutes % 60).padStart(2, '0')}${hour < 12 ? 'AM' : 'PM'}`;
}

function renderTimeline(index, selected) {
  const term = degreePaths.terms[index];
  const merged = new Map();
  function add(meeting, label, className) {
    if (meeting.begin == null || meeting.end == null) return;
    for (const day of meeting.days) {
      const key = `${day}:${meeting.begin}:${meeting.end}`;
      if (!merged.has(key)) merged.set(key, {day, begin: meeting.begin, end: meeting.end, labels: new Set(), classes: new Set()});
      merged.get(key).labels.add(label);
      merged.get(key).classes.add(className);
    }
  }
  for (const meeting of term.current) add(meeting, meeting.label + (meeting.mini ? ` M${meeting.mini}` : ''), 'timeline-current');
  for (const [id, optionId] of selected) {
    const course = degreePaths.courses[id];
    const option = term.options[id][optionId];
    for (const meeting of option.meetings) {
      add(meeting, `${course.id}${meeting.mini ? ' M' + meeting.mini : ''} [${meeting.section || option.label}] ${course.title}`,
        `timeline-course course-${course.fixed == null ? 'elective' : 'core'}`);
    }
  }
  const entries = [...merged.values()];
  const timeline = document.createElement('div');
  if (!entries.length) {
    timeline.className = 'timeline-empty';
    timeline.textContent = 'No meeting times detected.';
    return timeline;
  }
  timeline.className = 'timeline';
  const begin = Math.min(...entries.map(entry => entry.begin));
  const end = Math.max(...entries.map(entry => entry.end));
  const span = Math.max(end - begin, 1);
  const scale = document.createElement('div');
  scale.className = 'timeline-scale';
  for (const time of [begin, end]) {
    const label = document.createElement('span');
    label.textContent = formatMinutes(time);
    scale.append(label);
  }
  timeline.append(scale);
  for (const [day, label] of [['M', 'Mon'], ['T', 'Tue'], ['W', 'Wed'], ['R', 'Thu'], ['F', 'Fri'], ['S', 'Sat'], ['U', 'Sun']]) {
    const dayEntries = entries.filter(entry => entry.day === day).sort((a, b) => a.begin - b.begin || a.end - b.end);
    if (!dayEntries.length) continue;
    const row = document.createElement('div');
    row.className = 'timeline-day';
    const heading = document.createElement('div');
    heading.className = 'timeline-day-label';
    heading.textContent = label;
    const track = document.createElement('div');
    track.className = 'timeline-track';
    const laneEnds = [];
    for (const entry of dayEntries) {
      let lane = laneEnds.findIndex(time => entry.begin >= time);
      if (lane < 0) lane = laneEnds.length;
      laneEnds[lane] = entry.end;
      const bar = document.createElement('div');
      bar.className = 'timeline-bar ' + (entry.classes.size > 1 ? 'timeline-overlap' : [...entry.classes][0]);
      const text = [...entry.labels].join(' / ');
      const times = `${formatMinutes(entry.begin)}-${formatMinutes(entry.end)}`;
      bar.title = `${text}: ${times}`;
      bar.style.setProperty('--left', `${100 * (entry.begin - begin) / span}%`);
      bar.style.setProperty('--width', `${Math.max(100 * (entry.end - entry.begin) / span, 1.5)}%`);
      bar.style.setProperty('--lane', lane);
      for (const [className, value] of [['timeline-time', times], ['timeline-label', text]]) {
        const item = document.createElement('span');
        item.className = className;
        item.textContent = value;
        bar.append(item);
      }
      track.append(bar);
    }
    track.style.setProperty('--lanes', laneEnds.length);
    row.append(heading, track);
    timeline.append(row);
  }
  return timeline;
}

function renderSemester(index, selected) {
  const term = degreePaths.terms[index];
  const section = document.createElement('section');
  section.innerHTML = term.heading;
  const units = selected.reduce((total, [id]) => total + degreePaths.courses[id].units, 0);
  const underfilled = units !== term.cap;
  section.querySelector('.semester-heading').classList.toggle('semester-heading-underfilled', underfilled);
  const unitLabel = section.querySelector('.semester-units');
  unitLabel.classList.toggle('semester-unit-warning', underfilled);
  unitLabel.textContent = `(${units}/${term.cap} units)`;
  if (index === 0) section.append(renderTimeline(index, selected));
  const table = document.createElement('div');
  table.innerHTML = selected.length ? degreePaths.tableHead
    + selected.map(([course, option]) => term.options[course][option].row).join('') + '</tbody></table>'
    : '<p class="empty">No courses assigned.</p>';
  section.append(table);
  return section;
}
</script>
