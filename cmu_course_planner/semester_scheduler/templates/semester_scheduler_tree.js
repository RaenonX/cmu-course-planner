const sectionFilter = document.getElementById("section-filter");
let selectedSection;

function sectionFilterOptions() {
  const options = new Map();
  data.choices.forEach(choice => choice.components.forEach(component => {
    const key = JSON.stringify([choice.course, component]);
    options.set(key, {course: choice.course, component});
  }));
  return [...options.entries()].sort((left, right) =>
    left[1].course.localeCompare(right[1].course) ||
    left[1].component.localeCompare(right[1].component, undefined, {numeric: true})
  );
}

function populateSectionFilter() {
  sectionFilterOptions().forEach(([key, section]) => {
    const option = add(sectionFilter, "option", `${section.course} ${section.component}`);
    option.value = key;
  });
}

function scheduleMatchesSection(schedule) {
  if (!selectedSection) return true;
  return schedule.choices
    .map(choiceIndex => data.choices[choiceIndex])
    .some(choice =>
      choice.course === selectedSection.course &&
      choice.components.includes(selectedSection.component)
    );
}

function addLeaf(parent, schedule, index) {
  const leaf = add(parent, "div", undefined, "schedule-leaf");
  leaf.setAttribute("role", "treeitem");
  leaf.setAttribute("aria-selected", "false");
  leaf.tabIndex = 0;
  const selectLeaf = () => render(index, leaf);
  leaf.addEventListener("click", selectLeaf);
  leaf.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectLeaf();
    }
  });
  const choices = schedule.choices.map(choiceIndex => data.choices[choiceIndex]);
  choices.filter(choice => choice.role === "Elective").forEach(choice => {
    addCourseCode(leaf, choice, "schedule-course-code");
  });
  if (choices.some(choice => choice.online)) leaf.classList.add("has-online");
  const swaps = sectionSwaps(choices);
  const swapCount = `${swaps.length} swap${swaps.length === 1 ? "" : "s"}`;
  add(leaf, "span", `${swapCount} · ${gapStatsLabel(schedule)}`, "schedule-entry-metrics");
  leaf.title = [...continuityLines(schedule), sectionSwapLabel(swaps)].join("\n");
  const sections = choices.map(choice => `${choice.course} ${choice.bundle}`).join(", ");
  leaf.setAttribute("aria-label", `Section combination ${index + 1}: ${sections}`);
  return leaf;
}

function buildTree() {
  tree.replaceChildren();
  view.replaceChildren();
  selectedLeaf = undefined;
  const matching = data.schedules
    .map((schedule, index) => ({schedule, index}))
    .filter(({schedule}) => scheduleMatchesCourses(schedule) && scheduleMatchesSection(schedule));
  const groups = new Map();
  matching.forEach(({schedule, index}) => {
    const choices = schedule.choices.map(choiceIndex => data.choices[choiceIndex]);
    const key = choices
      .filter(choice => choice.role === "Elective")
      .map(choice => choice.course)
      .join("|");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({schedule, index, swapCount: sectionSwaps(choices).length});
  });

  let firstLeaf;
  let firstIndex;
  groups.forEach((schedules, key) => {
    const branch = add(tree, "details");
    branch.setAttribute("role", "treeitem");
    const count = schedules.length;
    const summary = add(branch, "summary", key.replaceAll("|", " + "));
    summary.setAttribute("aria-label", `${key.replaceAll("|", " plus ")}, ${count} section combinations`);
    const leaves = add(branch, "div", undefined, "schedule-branches");
    leaves.setAttribute("role", "group");
    schedules.sort((left, right) =>
      left.swapCount - right.swapCount ||
      left.schedule.totalGapMinutes - right.schedule.totalGapMinutes ||
      left.index - right.index
    );
    schedules.forEach(({schedule, index}) => {
      const leaf = addLeaf(leaves, schedule, index);
      if (!firstLeaf) {
        firstLeaf = leaf;
        firstIndex = index;
      }
    });
    if (firstLeaf && firstLeaf.parentElement === leaves) branch.open = true;
  });
  tree.setAttribute("role", "tree");
  if (firstLeaf) render(firstIndex, firstLeaf);
  else add(view, "p", "No schedules match the selected filters.", "semester-unit-warning");
}

sectionFilter.addEventListener("change", () => {
  if (!sectionFilter.value) {
    selectedSection = undefined;
  } else {
    const [course, component] = JSON.parse(sectionFilter.value);
    selectedSection = {course, component};
  }
  buildTree();
});

populateCourseFilter();
populateSectionFilter();
buildTree();
