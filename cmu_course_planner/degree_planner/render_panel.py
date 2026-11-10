import html

from .route_filters import route_filters


def build_schedule_panel(index, name, description, courses):
    active = " active" if index == 0 else ""
    return (
        f'<div id="tab-{index}" class="tab-panel{active}" data-variant="{index}">'
        f'<p class="variant-desc">{html.escape(description)}</p>'
        '<p class="route-count">Generating all valid paths in your browser… '
        'including lighter schedules</p>'
        '<div class="route-layout"><nav class="route-browser" aria-label="Schedule route selection">'
        '<h2>Schedule tree</h2>' + route_filters(courses)
        + '<div class="route-tree" role="tree"></div></nav>'
        '<section class="route-panel" aria-live="polite"></section></div></div>'
    )
