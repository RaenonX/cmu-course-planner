import html as html_lib

from ..common.labels import category_badges, mini_label, prereq_info
from ..common.paths import REPORT_TEMPLATE_DIR
from ..common.rating import parse_rating, star_rating

def _sem_chips(semesters: list[str], offering_map: dict[str, dict | None]) -> str:
    """
    Render semester chips in chronological order (oldest first).
    Offered chips are colored links; not-offered chips are dim.
    """
    parts = ['<div class="chips">']
    for sem in reversed(semesters):  # reverse newest-first → oldest-first
        info = offering_map.get(sem)
        sem_type = sem[0]  # F, M, S
        label = sem        # e.g. F25
        if info is not None:
            mini_html = (
                f'<span class="mini">{mini_label(info["minis"])}</span>'
                if info["minis"] else ""
            )
            parts.append(
                f'<a class="chip chip-{sem_type}" href="{info["link"]}" target="_blank">'
                f'{label}{mini_html}</a>'
            )
        else:
            parts.append(f'<span class="chip chip-off">{label}</span>')
    parts.append("</div>")
    return "".join(parts)

def _meeting_label(meeting: dict[str, str]) -> str:
    mini = f'M{meeting["mini"]} ' if meeting.get("mini") else ""
    return f'{mini}{meeting["days"]} {meeting["begin"]}-{meeting["end"]}'

def _offering_times(semesters: list[str], offering_map: dict[str, dict | None]) -> str:
    parts = []
    for sem in reversed(semesters):  # reverse newest-first -> oldest-first
        info = offering_map.get(sem)
        if not info:
            continue
        meetings = info.get("meetings") or []
        if not meetings:
            continue
        labels = ", ".join(_meeting_label(m) for m in meetings)
        parts.append(f'<div><strong>{sem}</strong>: {html_lib.escape(labels)}</div>')
    return "".join(parts) if parts else '<span class="no-prereqs">Unknown</span>'


def build_report_html(rows_html: list[str], today, years: int, teaching_location: str) -> str:
    head = (REPORT_TEMPLATE_DIR / "report_head.html").read_text(encoding="utf-8")
    head = (
        head.replace("{{DATE}}", today.strftime("%Y-%m-%d"))
        .replace("{{YEARS}}", str(years))
        .replace("{{LOCATION}}", html_lib.escape(teaching_location))
    )
    tail = (REPORT_TEMPLATE_DIR / "report_tail.html").read_text(encoding="utf-8")
    return head + "\n".join(rows_html) + "\n" + tail


def build_report_rows(valid_entries: list[dict], course_info: dict, results: dict, semesters: list[str]) -> list[str]:
    rows_html: list[str] = []
    for entry in valid_entries:
        cid = entry["course"]
        title, units, prerequisites = course_info[cid]
        cats = entry.get("category") or []
        rating, _ = parse_rating(entry.get("rating"), cid)
        offering_map = {sem: results.get((cid, sem)) for sem in semesters}
        rows_html.append(
            f"  <tr>\n"
            f'    <td class="course">{cid}</td>\n'
            f"    <td>{title}</td>\n"
            f"    <td>{units}</td>\n"
            f'    <td data-sort="{rating}" title="{rating}/5">{star_rating(rating)}</td>\n'
            f"    <td>{category_badges(cats)}</td>\n"
            f"    <td>{prereq_info(prerequisites)}</td>\n"
            f'    <td class="times">{_offering_times(semesters, offering_map)}</td>\n'
            f"    <td>{_sem_chips(semesters, offering_map)}</td>\n"
            f"  </tr>"
        )
    return rows_html
