import html

from .route_tree import Route


def route_filters(routes: list[Route]) -> str:
    courses = {
        course.course: course.title
        for schedule, _ in routes
        for semester in schedule
        for course in semester
        if course.fixed_semester is None
    }
    options = "".join(
        f'<label><select data-course="{html.escape(code)}">'
        '<option value="optional">Optional</option>'
        '<option value="required">Required</option>'
        '<option value="excluded">Excluded</option>'
        f'</select><span>{html.escape(code)} — '
        f'{html.escape(title)}</span></label>'
        for code, title in sorted(courses.items())
    )
    return (
        '<fieldset class="route-course-filter"><legend>Elective preferences</legend>'
        f'<div class="route-course-options">{options}</div></fieldset>'
        '<button class="clear-route-courses" type="button" disabled>Reset to optional</button>'
    )
