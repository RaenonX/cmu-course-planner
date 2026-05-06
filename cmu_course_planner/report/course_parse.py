import html as html_lib
import re

def _parse_course_info(html: str) -> tuple[str, int]:
    """Heuristically extract title and unit count from a course-details page."""
    def clean(value: str) -> str:
        value = re.sub(r'<[^>]+>', ' ', value)
        value = html_lib.unescape(value)
        return re.sub(r'\s+', ' ', value).strip()

    title = "Unknown"
    m = re.search(r'data-maintitle=(["\'])(.*?)\1', html, re.IGNORECASE | re.DOTALL)
    if m:
        main_title = clean(m.group(2))
        title_match = re.match(r'\d{5}\s+(.+)', main_title)
        title = title_match.group(1).strip() if title_match else main_title

    text = clean(html)
    for pattern in [
        r'Title\s*:?\s*([A-Z][^:\n\r]{4,100}?)(?:\s{2,}|Units)',
        r'\d{2}-\d{3}\s+([A-Z][^:\n\r]{4,100}?)(?:\s{2,}|\n)',
    ]:
        if title != "Unknown":
            break
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            title = m.group(1).strip().rstrip(' -|')
            break

    units = 0
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    for table in tables:
        header_match = re.search(r'<thead[^>]*>(.*?)</thead>', table, re.DOTALL | re.IGNORECASE)
        if not header_match:
            continue

        headers = [
            clean(cell)
            for cell in re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL | re.IGNORECASE)
        ]
        try:
            units_idx = next(i for i, header in enumerate(headers) if header.lower() == "units")
        except StopIteration:
            continue

        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
        for row in rows:
            cells = [
                clean(cell)
                for cell in re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            ]
            if units_idx >= len(cells):
                continue
            m = re.match(r'^(\d+(?:\.\d+)?)$', cells[units_idx])
            if m:
                units = int(float(m.group(1)))
                break
        if units:
            break

    for pattern in [
        r'[Uu]nits?\s*:?\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*[Uu]nits',
    ]:
        if units:
            break
        m = re.search(pattern, text)
        if m:
            units = int(float(m.group(1)))
            break

    return title, units

def _parse_prerequisites(html: str) -> str:
    """Extract the SOC course-details prerequisite text."""
    def clean(value: str) -> str:
        value = re.sub(r'<[^>]+>', ' ', value)
        value = html_lib.unescape(value)
        return re.sub(r'\s+', ' ', value).strip()

    m = re.search(
        r'<dt>\s*Prerequisites\s*</dt>\s*<dd>(.*?)</dd>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return "Unknown"

    prereqs = clean(m.group(1))
    return prereqs if prereqs else "None"
