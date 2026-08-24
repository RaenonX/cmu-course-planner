import html
import json

from .models import Course, Meeting
from .what_if import build_what_if_data


def what_if_panel(
    panel_id: str,
    semesters: list[str],
    schedule: list[list[Course]],
    unplaced: list[Course],
    unit_caps: list[int],
    current_time_ranges: list[Meeting],
) -> str:
    data = json.dumps(
        build_what_if_data(semesters, schedule, unplaced, unit_caps, current_time_ranges),
        ensure_ascii=False,
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    course_options = "".join(
        f'<option value="{html.escape(course.course)}">'
        f'{html.escape(course.course)} — {html.escape(course.title)}</option>'
        for course in unplaced
    )
    return f"""
<div class="what-if" id="{panel_id}">
  <div class="what-if-heading">
    <div><h4>What if?</h4><p>Try adding a course directly or swapping out one scheduled course.</p></div>
  </div>
  <div class="what-if-controls">
    <label>Course<select class="what-if-course">{course_options}</select></label>
    <label>Semester<select class="what-if-semester"></select></label>
    <label>Change<select class="what-if-swap"></select></label>
  </div>
  <div class="what-if-result" role="status" aria-live="polite"></div>
  <script type="application/json" class="what-if-data">{data}</script>
</div>
"""
