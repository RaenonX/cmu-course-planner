import html as html_lib

from .models import Course
from .route_labels import _route_leaf_label, _route_semester_label

Route = tuple[list[list[Course]], list[Course]]
RouteEntry = tuple[int, list[list[Course]]]


def route_tree(routes: list[Route], prefer: list[str]) -> str:
    if not routes:
        return '<p class="empty">No routes generated.</p>\n'
    entries = [(route_idx, route[0]) for route_idx, route in enumerate(routes)]

    def build(level: int, branch_entries: list[RouteEntry]) -> str:
        if level == len(branch_entries[0][1]):
            return "".join(
                f'<button class="route-tree-leaf{" is-selected" if route_idx == 0 else ""}" '
                f'data-route-index="{route_idx}" role="treeitem" '
                f'aria-selected="{"true" if route_idx == 0 else "false"}">'
                f'{_route_leaf_label(route_idx, schedule, prefer)}</button>\n'
                for route_idx, schedule in branch_entries
            )

        groups: dict[tuple[str, ...], list[RouteEntry]] = {}
        for entry in branch_entries:
            signature = tuple(sorted(course.course for course in entry[1][level]))
            groups.setdefault(signature, []).append(entry)

        parts = []
        for group_idx, group_entries in enumerate(groups.values()):
            schedule = group_entries[0][1]
            route_count = len(group_entries)
            label = _route_semester_label(schedule[level])
            parts.append(
                f'<details class="route-tree-branch" role="treeitem"'
                f'{" open" if group_idx == 0 else ""}>'
                f'<summary><span>Semester {level + 1} · {html_lib.escape(label)}</span>'
                f'<span class="route-tree-count">{route_count} '
                f'route{"s" if route_count != 1 else ""}</span></summary>'
                f'<div class="route-tree-children" role="group">{build(level + 1, group_entries)}</div>'
                '</details>\n'
            )
        return "".join(parts)

    return f'<div class="route-tree" role="tree">{build(0, entries)}</div>\n'
