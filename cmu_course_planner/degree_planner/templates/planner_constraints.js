function selectedUnits(data, selected) {
  return selected.reduce((total, [course]) => total + data.courses[course].units, 0);
}

function withinCapacity(data, index, selected) {
  const term = data.terms[index];
  if (selected.some(([course, option]) => !term.slots[course].includes(term.options[course][option].mini))) return false;
  if (selectedUnits(data, selected) > term.cap) return false;
  return term.minis.every(mini => selected.reduce((load, [course, option]) => {
    const slot = term.options[course][option].mini;
    return load + (slot == null ? data.courses[course].units
      : slot === mini ? 2 * data.courses[course].units : 0);
  }, 0) <= term.cap);
}

function continuity(data, index, selected) {
  const term = data.terms[index];
  const buckets = new Map();
  const meetings = [...term.current, ...selected.flatMap(([course, option]) => term.options[course][option].meetings)];
  for (const meeting of meetings) {
    if (meeting.begin == null || meeting.end == null) continue;
    for (const day of meeting.days) {
      for (const mini of meeting.mini == null ? term.minis : [meeting.mini]) {
        const key = `${day}:${mini}`;
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push([meeting.begin, meeting.end]);
      }
    }
  }
  let overlap = 0;
  let gap = 0;
  for (const intervals of buckets.values()) {
    intervals.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    let previous = null;
    for (const [begin, end] of intervals) {
      if (previous != null) {
        overlap += Math.max(previous - begin, 0);
        gap += Math.max(begin - previous, 0);
      }
      previous = Math.max(previous ?? end, end);
    }
  }
  return {overlap, gap};
}

function meetingsOverlap(a, b) {
  return a.begin != null && b.begin != null && a.end != null && b.end != null
    && a.days.some(day => b.days.includes(day))
    && (a.mini == null || b.mini == null || a.mini === b.mini)
    && a.begin < b.end && b.begin < a.end;
}

function conflictLabels(data, index, selected, course, option) {
  const term = data.terms[index];
  const existing = [
    ...term.current.map(meeting => [meeting.label, meeting]),
    ...selected.flatMap(([c, o]) => term.options[c][o].meetings.map(meeting => [data.courses[c].id, meeting])),
  ];
  return [...new Set(term.options[course][option].meetings.flatMap(candidate =>
    existing.filter(([, meeting]) => meetingsOverlap(candidate, meeting))
      .map(([label, meeting]) => `${label} (${meeting.text})`)))];
}
