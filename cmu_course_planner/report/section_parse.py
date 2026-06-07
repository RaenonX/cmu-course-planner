import html as html_lib
import re

_MINI_RE = re.compile(r'^.+([1-6])$')

def _clean_cell(value: str) -> str:
    value = re.sub(r'<[^>]+>', ' ', value)
    value = html_lib.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()

def _section_rows(html: str, teaching_location: str) -> list[list[str]]:
    """
    Return section rows matching teaching_location.

    Older or changed SOC pages may not expose a Teaching Location column. In that
    case, preserve the existing behavior and treat all section rows as matching.
    """
    matching_rows: list[list[str]] = []
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    for table in tables:
        header_match = re.search(r'<thead[^>]*>(.*?)</thead>', table, re.DOTALL | re.IGNORECASE)
        headers = (
            [_clean_cell(cell) for cell in re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL | re.IGNORECASE)]
            if header_match else []
        )
        location_idx = next(
            (
                i for i, header in enumerate(headers)
                if "teaching location" in header.lower() or header.lower() == "location"
            ),
            None,
        )
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
        for row in rows:
            cells = [_clean_cell(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)]
            if len(cells) < 7:
                continue
            if location_idx is not None and location_idx < len(cells):
                if cells[location_idx] != teaching_location:
                    continue
            matching_rows.append(cells)
    return matching_rows

def _parse_minis(section_rows: list[list[str]]) -> list[int]:
    """Scan matching section rows and return sorted mini slot numbers (empty = full semester)."""
    found: set[int] = set()
    for row in section_rows:
        for cell in row:
            m = _MINI_RE.match(cell)
            if m:
                found.add(int(m.group(1)))
    return sorted(found)

def _section_mini(section: str, is_mini: bool) -> int | None:
    if not is_mini:
        return None
    m = _MINI_RE.match(section)
    return int(m.group(1)) if m else None

def _parse_meetings(html: str, teaching_location: str) -> list[dict[str, str]]:
    """Extract unique meeting times from section rows matching teaching_location."""
    meetings: list[dict] = []
    seen: set[tuple[str, str, str, int | None]] = set()
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    for table in tables:
        header_match = re.search(r'<thead[^>]*>(.*?)</thead>', table, re.DOTALL | re.IGNORECASE)
        if not header_match:
            continue
        headers = [
            _clean_cell(cell).lower()
            for cell in re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL | re.IGNORECASE)
        ]
        location_idx = next(
            (
                i for i, header in enumerate(headers)
                if "teaching location" in header or header == "location"
            ),
            None,
        )
        try:
            days_idx = next(i for i, header in enumerate(headers) if header == "days")
            begin_idx = next(i for i, header in enumerate(headers) if header == "begin")
            end_idx = next(i for i, header in enumerate(headers) if header == "end")
        except StopIteration:
            continue
        section_idx = next(
            (
                i for i, header in enumerate(headers)
                if header in {"section", "lec/sec", "lec / sec"}
            ),
            None,
        )
        mini_idx = next((i for i, header in enumerate(headers) if header == "mini"), None)

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
        for row in rows:
            cells = [_clean_cell(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)]
            if max(days_idx, begin_idx, end_idx) >= len(cells):
                continue
            if location_idx is not None and location_idx < len(cells):
                if cells[location_idx] != teaching_location:
                    continue
            days = cells[days_idx]
            begin = cells[begin_idx]
            end = cells[end_idx]
            if not days or not begin or not end or "tba" in {days.lower(), begin.lower(), end.lower()}:
                continue
            section = cells[section_idx] if section_idx is not None and section_idx < len(cells) else ""
            mini_value = cells[mini_idx] if mini_idx is not None and mini_idx < len(cells) else ""
            is_mini = mini_value.upper() == "Y" or bool(_MINI_RE.match(section))
            mini = _section_mini(section, is_mini)
            key = (days, begin, end, mini)
            if key in seen:
                continue
            seen.add(key)
            meeting = {"days": days, "begin": begin, "end": end}
            if mini is not None:
                meeting["mini"] = mini
            meetings.append(meeting)
    return meetings
