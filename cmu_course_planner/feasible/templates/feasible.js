const data = JSON.parse(document.getElementById("schedule-data").textContent);
const tree = document.getElementById("schedule-tree");
const view = document.getElementById("schedule-view");
const dayNames = {M: "Mon", T: "Tue", W: "Wed", R: "Thu", F: "Fri", S: "Sat", U: "Sun"};
let selectedLeaf;
let activeCourseCode;

function add(parent, tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  parent.appendChild(element);
  return element;
}

const coursePopover = add(document.body, "div", undefined, "course-popover");
coursePopover.id = "course-popover";
coursePopover.setAttribute("role", "tooltip");
coursePopover.hidden = true;

function hideCoursePopover() {
  coursePopover.hidden = true;
  if (activeCourseCode) activeCourseCode.setAttribute("aria-expanded", "false");
  activeCourseCode = undefined;
}

function showCoursePopover(button, choice) {
  hideCoursePopover();
  activeCourseCode = button;
  button.setAttribute("aria-expanded", "true");
  coursePopover.textContent = choice.title;
  coursePopover.className = `course-popover course-${choice.role.toLowerCase()}`;
  coursePopover.hidden = false;
  const rect = button.getBoundingClientRect();
  const left = Math.max(8, Math.min(rect.left, window.innerWidth - coursePopover.offsetWidth - 8));
  let top = rect.bottom + 8;
  if (top + coursePopover.offsetHeight > window.innerHeight - 8) {
    top = rect.top - coursePopover.offsetHeight - 8;
  }
  coursePopover.style.left = `${left}px`;
  coursePopover.style.top = `${Math.max(8, top)}px`;
}

function addCourseCode(parent, choice, className, onSelect) {
  const button = add(parent, "button", choice.course, `course-code${className ? ` ${className}` : ""}`);
  if (choice.online) button.classList.add("is-online");
  button.type = "button";
  button.setAttribute("aria-controls", coursePopover.id);
  button.setAttribute("aria-expanded", "false");
  button.addEventListener("click", event => {
    event.stopPropagation();
    if (onSelect) onSelect();
    showCoursePopover(button, choice);
  });
  return button;
}

document.addEventListener("click", hideCoursePopover);
document.addEventListener("keydown", event => {
  if (event.key === "Escape") hideCoursePopover();
});
window.addEventListener("resize", hideCoursePopover);
window.addEventListener("scroll", hideCoursePopover, true);

function prerequisiteLabel(choice) {
  const status = choice.prerequisiteStatus;
  if (status === "none") return "None";
  if (status === "satisfied") return "Satisfied";
  if (status === "unsatisfied") return `Unsatisfied — advisory: ${choice.prerequisites}`;
  return `Unknown — advisory: ${choice.prerequisites}`;
}

function renderPickedCourses(choices) {
  add(view, "h2", "Selected courses");
  const picked = add(view, "div", undefined, "picked-courses");
  choices.forEach(choice => {
    const chip = add(picked, "span", undefined, `course-chip course-${choice.role.toLowerCase()}`);
    addCourseCode(chip, choice);
  });
}

function renderTable(choices) {
  const table = add(view, "table");
  const head = add(add(table, "thead"), "tr");
  ["Role", "Course", "Title", "Units", "Complete section bundle", "Prerequisite", "Exact meetings"]
    .forEach(label => add(head, "th", label));
  const body = add(table, "tbody");
  choices.forEach(choice => {
    const row = add(body, "tr", undefined, `course-${choice.role.toLowerCase()}`);
    add(row, "td", choice.role);
    const courseCell = add(row, "td");
    addCourseCode(courseCell, choice);
    const meetings = choice.meetings.length
      ? choice.meetings.map(item => `${item.section}: ${item.daysLabel} ${item.begin}–${item.end}`).join(", ")
      : "TBA / incomplete";
    [choice.title, choice.units, choice.bundle, prerequisiteLabel(choice), meetings]
      .forEach(value => add(row, "td", String(value)));
  });
}

function timeLabel(minutes) {
  const hour = Math.floor(minutes / 60);
  const minute = String(minutes % 60).padStart(2, "0");
  return `${hour % 12 || 12}:${minute}${hour < 12 ? "AM" : "PM"}`;
}

function renderTimeline(choices, mini) {
  add(view, "h4", `Mini ${mini}`);
  const entries = [];
  choices.forEach(choice => choice.meetings.forEach(meeting => {
    if ((meeting.mini === null || meeting.mini === mini) && meeting.beginMinutes !== null) {
      meeting.days.forEach(day => entries.push({...meeting, day, choice}));
    }
  }));
  if (!entries.length) return add(view, "p", "No meeting times detected.", "timeline-empty");
  const begin = Math.min(...entries.map(item => item.beginMinutes));
  const end = Math.max(...entries.map(item => item.endMinutes));
  const span = Math.max(end - begin, 1);
  const timeline = add(view, "div", undefined, "timeline");
  const scale = add(timeline, "div", undefined, "timeline-scale");
  add(scale, "span", timeLabel(begin));
  add(scale, "span", timeLabel(end));
  Object.keys(dayNames).forEach(day => {
    const dayEntries = entries.filter(item => item.day === day)
      .sort((a, b) => a.beginMinutes - b.beginMinutes || a.endMinutes - b.endMinutes);
    if (!dayEntries.length) return;
    const row = add(timeline, "div", undefined, "timeline-day");
    add(row, "div", dayNames[day], "timeline-day-label");
    const track = add(row, "div", undefined, "timeline-track");
    const laneEnds = [];
    dayEntries.forEach(item => {
      let lane = laneEnds.findIndex(laneEnd => item.beginMinutes >= laneEnd);
      if (lane < 0) lane = laneEnds.length;
      laneEnds[lane] = item.endMinutes;
      const bar = add(track, "div", undefined, `timeline-bar timeline-course course-${item.choice.role.toLowerCase()}`);
      bar.style.setProperty("--left", `${((item.beginMinutes - begin) / span) * 100}%`);
      bar.style.setProperty("--width", `${Math.max(((item.endMinutes - item.beginMinutes) / span) * 100, 1.5)}%`);
      bar.style.setProperty("--lane", String(lane));
      add(bar, "span", `${timeLabel(item.beginMinutes)}-${timeLabel(item.endMinutes)}`, "timeline-time");
      const label = add(bar, "span", undefined, "timeline-label");
      addCourseCode(label, item.choice);
      label.append(` [${item.section}] ${item.choice.title}`);
    });
    track.style.setProperty("--lanes", String(laneEnds.length));
  });
}

const continuityDayNames = {M: "M", T: "Tu", W: "W", R: "Th", F: "F", S: "Sa", U: "Su"};

function continuityTimeLabel(minutes) {
  const hour = Math.floor(minutes / 60);
  const minute = String(minutes % 60).padStart(2, "0");
  return `${hour % 12 || 12}:${minute} ${hour < 12 ? "AM" : "PM"}`;
}

function gapLabel(minutes) {
  return minutes === 0 ? "No Gap" : `Gap ${minutes} mins`;
}

function gapStatsLabel(schedule) {
  return `Gap: Total ${schedule.totalGapMinutes} mins · Max ${schedule.maxGapMinutes} mins`;
}

function continuityLines(schedule) {
  const lines = [];
  schedule.continuity.forEach(mini => {
    lines.push(`Mini ${mini.mini}`);
    mini.groups.forEach(group => {
      const days = group.days.map(day => continuityDayNames[day]).join(", ");
      lines.push(
        `${days}: ${continuityTimeLabel(group.beginMinutes)} ~ ${continuityTimeLabel(group.endMinutes)} / ${gapLabel(group.gapMinutes)}`
      );
    });
  });
  lines.push(gapStatsLabel(schedule));
  return lines;
}

function sameComponents(left, right) {
  const orderedLeft = [...left].sort();
  const orderedRight = [...right].sort();
  return orderedLeft.length === orderedRight.length &&
    orderedLeft.every((component, index) => component === orderedRight[index]);
}

function sectionSwaps(choices) {
  return choices.flatMap(choice => {
    const current = data.currentSections[choice.course];
    if (choice.role !== "Core" || !current) return [];
    if (sameComponents(current, choice.components)) return [];
    return [{
      course: choice.course,
      current: current.join(" + "),
      selected: choice.components.join(" + "),
    }];
  });
}

function sectionSwapLabel(swaps) {
  if (!swaps.length) return "No section swaps";
  return swaps.map(swap => `${swap.course}: ${swap.current} → ${swap.selected}`).join(" · ");
}

function renderContinuity(schedule) {
  const panel = add(view, "section", undefined, "continuity-panel");
  add(panel, "h3", "Time continuity");
  schedule.continuity.forEach(mini => {
    add(panel, "h4", `Mini ${mini.mini}`);
    mini.groups.forEach(group => {
      const row = add(panel, "p", undefined, "continuity-row");
      const days = group.days.map(day => continuityDayNames[day]).join(", ");
      add(row, "span", `${days}:`);
      add(
        row,
        "span",
        `${continuityTimeLabel(group.beginMinutes)} ~ ${continuityTimeLabel(group.endMinutes)} / ${gapLabel(group.gapMinutes)}`,
      );
    });
  });
  add(panel, "p", gapStatsLabel(schedule), "continuity-total");
}

function renderSectionSwaps(choices) {
  const swaps = sectionSwaps(choices);
  const panel = add(view, "section", undefined, "continuity-panel section-swaps-panel");
  add(panel, "h3", "Section swaps needed");
  if (!swaps.length) {
    add(panel, "p", "No section swaps needed.");
    return;
  }
  const list = add(panel, "ul", undefined, "section-swap-list");
  swaps.forEach(swap => add(list, "li", `${swap.course}: ${swap.current} → ${swap.selected}`));
}

function render(index, leaf) {
  hideCoursePopover();
  view.replaceChildren();
  const schedule = data.schedules[index];
  const choices = schedule.choices.map(choiceIndex => data.choices[choiceIndex]);
  renderPickedCourses(choices);
  add(view, "p", `${schedule.electiveUnits} elective units · ${schedule.totalUnits} total units`, "meta");
  if (schedule.unknownTime) add(view, "p", "Time incomplete — this schedule cannot be fully conflict-verified.", "semester-unit-warning");
  if (schedule.prerequisiteAdvisory) add(view, "p", "One or more prerequisite results are advisory; review the marked courses.", "semester-unit-warning");
  renderContinuity(schedule);
  renderSectionSwaps(choices);
  add(view, "h3", "Sections and meetings");
  renderTable(choices);
  data.minis.forEach(mini => renderTimeline(choices, mini));
  if (selectedLeaf) {
    selectedLeaf.classList.remove("is-selected");
    selectedLeaf.setAttribute("aria-selected", "false");
  }
  selectedLeaf = leaf;
  selectedLeaf.classList.add("is-selected");
  selectedLeaf.setAttribute("aria-selected", "true");
}
