import re

from .html_table import clean_cell, data_rows, header_cells, header_index, tables


def _parse_title(html: str) -> str:
    """Heuristically extract the course title from a course-details page."""
    match = re.search(r'data-maintitle=(["\'])(.*?)\1', html, re.IGNORECASE | re.DOTALL)
    if match:
        main_title = clean_cell(match.group(2))
        title_match = re.match(r'\d{5}\s+(.+)', main_title)
        return title_match.group(1).strip() if title_match else main_title

    text = clean_cell(html)
    for pattern in (
        r'Title\s*:?\s*([A-Z][^:\n\r]{4,100}?)(?:\s{2,}|Units)',
        r'\d{2}-\d{3}\s+([A-Z][^:\n\r]{4,100}?)(?:\s{2,}|\n)',
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(' -|')
    return "Unknown"


def _units_from_tables(html: str) -> int:
    """Unit count read from the Units column of any course table, or 0."""
    for table in tables(html):
        units_idx = header_index(header_cells(table), "units")
        if units_idx is None:
            continue
        for cells in data_rows(table):
            if units_idx >= len(cells):
                continue
            match = re.match(r'^(\d+(?:\.\d+)?)$', cells[units_idx])
            if match:
                return int(float(match.group(1)))
    return 0


def _parse_units(html: str) -> int:
    """Extract the unit count, preferring the table column over inline text."""
    units = _units_from_tables(html)
    if units:
        return units
    text = clean_cell(html)
    for pattern in (r'[Uu]nits?\s*:?\s*(\d+(?:\.\d+)?)', r'(\d+(?:\.\d+)?)\s*[Uu]nits'):
        match = re.search(pattern, text)
        if match:
            return int(float(match.group(1)))
    return 0


def _parse_course_info(html: str) -> tuple[str, int]:
    """Heuristically extract title and unit count from a course-details page."""
    return _parse_title(html), _parse_units(html)


def _parse_prerequisites(html: str) -> str:
    """Extract the SOC course-details prerequisite text."""
    match = re.search(
        r'<dt>\s*Prerequisites\s*</dt>\s*<dd>(.*?)</dd>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return "Unknown"
    prereqs = clean_cell(match.group(1))
    return prereqs if prereqs else "None"
