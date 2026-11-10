function courseWarnings(course, option) {
  const warnings = [];
  if (course.prerequisiteStatus === 'unsatisfied') warnings.push(`Prerequisite is marked unsatisfied: ${course.prerequisites}.`);
  if (course.prerequisiteStatus === 'unknown') warnings.push(`Prerequisite eligibility could not be determined: ${course.prerequisites}.`);
  if (option?.unresolved) warnings.push('The selected section has TBA or incomplete meeting-time data.');
  return warnings;
}

function analyzeClientSwap(data, index, selected, courseId, remove = null) {
  const term = data.terms[index];
  const course = data.courses[courseId];
  const remaining = selected.filter(([id]) => id !== remove);
  const total = selectedUnits(data, remaining) + course.units;
  const base = {
    remove: remove == null ? '' : data.courses[remove].id,
    removeLabel: remove == null ? 'Keep all scheduled courses' : `Remove ${data.courses[remove].label}`,
    unitsAfter: total,
  };
  const rejected = (summary, reasons) => ({...base, status: 'rejected', summary, reasons, warnings: courseWarnings(course)});
  if (!term.options[courseId].length) return rejected('No detected offering', ['This course has no detected offering for this semester type.']);
  if (total > term.cap) return rejected('The selected replacement does not fit', [
    `Unit limit exceeded: ${total}/${term.cap} units after removing ${remove == null ? 0 : data.courses[remove].units} and adding ${course.units}.`,
  ]);
  const options = term.options[courseId].map((_, option) => option)
    .filter(option => withinCapacity(data, index, [...remaining, [courseId, option]]));
  if (!options.length) return rejected('The selected replacement does not fit', [
    `Mini workload limit exceeded: every placement exceeds ${term.cap} nominal hours/week in at least one half of the semester.`,
  ]);
  const overlap = continuity(data, index, remaining).overlap;
  const reasons = [];
  for (const id of options) {
    const option = term.options[courseId][id];
    if (continuity(data, index, [...remaining, [courseId, id]]).overlap === overlap) return {
      ...base, status: 'works', summary: `${total}/${term.cap} units · Section ${option.label}${option.mini ? ', Mini ' + option.mini : ''}`,
      reasons: [], warnings: courseWarnings(course, option),
    };
    const conflicts = conflictLabels(data, index, remaining, courseId, id);
    reasons.push(`Section ${option.label}${option.mini ? ' (Mini ' + option.mini + ')' : ''}: ${conflicts.length ? 'conflicts with ' + conflicts.join(', ') : 'contains overlapping meeting times'}.`);
  }
  return rejected('The selected replacement does not fit', reasons);
}

function routeWhatIf(data, terms, choices) {
  const schedule = choices.map((choice, index) => terms[index].choices[choice]);
  const assigned = new Set(schedule.flatMap(selected => selected.map(([course]) => course)));
  return {
    unitCaps: data.unitCaps,
    courses: data.courses.flatMap((course, id) => assigned.has(id) ? [] : [{
      id: course.id, label: course.label,
      semesters: schedule.map((selected, index) => ({
        index, label: data.terms[index].label, offered: data.terms[index].options[id].length > 0,
        swaps: [analyzeClientSwap(data, index, selected, id),
          ...selected.filter(([c]) => data.courses[c].fixed == null)
            .map(([remove]) => analyzeClientSwap(data, index, selected, id, remove))],
      })),
    }]),
  };
}
