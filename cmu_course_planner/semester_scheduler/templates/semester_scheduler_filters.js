const courseFilterOptions = document.getElementById("course-filter-options");
const clearCourseFilter = document.getElementById("clear-course-filter");
const coursePreferences = new Map();

function scheduleMatchesCourses(schedule) {
  const courses = new Set(schedule.choices.map(index => data.choices[index].course));
  return [...coursePreferences].every(([course, preference]) =>
    preference === "required" ? courses.has(course) : !courses.has(course));
}

function populateCourseFilter() {
  const courses = new Map(data.choices.map(choice => [choice.course, choice]));
  [...courses.values()].sort((a, b) => a.course.localeCompare(b.course)).forEach(choice => {
    const label = add(courseFilterOptions, "label");
    const select = add(label, "select");
    select.dataset.preference = "optional";
    ["optional", "required", "excluded"].forEach(value => {
      const option = add(select, "option", value[0].toUpperCase() + value.slice(1));
      option.value = value;
    });
    add(label, "span", `${choice.course} — ${choice.title}`);
    select.addEventListener("change", () => {
      select.dataset.preference = select.value;
      if (select.value === "optional") coursePreferences.delete(choice.course);
      else coursePreferences.set(choice.course, select.value);
      clearCourseFilter.disabled = coursePreferences.size === 0;
      buildTree();
    });
  });
  clearCourseFilter.disabled = true;
}

clearCourseFilter.addEventListener("click", () => {
  coursePreferences.clear();
  courseFilterOptions.querySelectorAll("select").forEach(select => {
    select.value = "optional";
    select.dataset.preference = "optional";
  });
  clearCourseFilter.disabled = true;
  buildTree();
});
