import re

from .html_table import data_rows, header_cells, header_index, tables
from .section_options import build_section_options

# Trailing digit of a section code identifies its mini slot, e.g. "A4" -> 4.
_MINI_RE = re.compile(r'([1-6])$')
# A clock time such as "11:00AM"; used to locate the Begin/End columns in a row.
_TIME_RE = re.compile(r'\d{1,2}:\d{2}\s*[AP]M', re.IGNORECASE)


def _section_mini(section: str, mini_flag: str) -> int | None:
    """
    Mini-slot number for a section, or None for full-semester sections.

    The Mini column ("Y") is authoritative: only sections explicitly flagged as
    minis are treated as such, and the slot number is the trailing digit of the
    section code (e.g. "A4" -> 4). A full-semester lecture like "Lec 1" has an
    empty Mini column and is never treated as a mini even though its label ends
    in a digit — mistaking it for mini 1 hides genuine time conflicts.
    """
    if mini_flag.strip().upper() != "Y":
        return None
    match = _MINI_RE.search(section)
    return int(match.group(1)) if match else None


def _column_offsets(headers: list[str]) -> dict[str, int] | None:
    """
    Offset of each known column relative to the Begin column, or None when the
    table is not a section table (missing Days/Begin/End headers).

    Offsets are anchored on Begin so each row can be aligned by finding its
    begin-time cell. This tolerates extra leading cells (e.g. the summer
    "session" column) that shift every column right by the same amount.
    """
    begin = header_index(headers, "begin")
    days = header_index(headers, "days")
    end = header_index(headers, "end")
    if begin is None or days is None or end is None:
        return None
    offsets = {"days": days - begin, "end": end - begin}
    section = header_index(headers, "section", "lec/sec", "lec / sec")
    if section is not None:
        offsets["section"] = section - begin
    mini = header_index(headers, "mini")
    if mini is not None:
        offsets["mini"] = mini - begin
    location = header_index(headers, "teaching location", "location", contains=True)
    if location is not None:
        offsets["location"] = location - begin
    return offsets


def _cell_at(cells: list[str], begin_idx: int, offsets: dict[str, int], name: str) -> str | None:
    """Cell for column ``name`` relative to the begin-time cell, or None if absent."""
    if name not in offsets:
        return None
    index = begin_idx + offsets[name]
    return cells[index] if 0 <= index < len(cells) else None


def _section_record(cells: list[str], offsets: dict[str, int], teaching_location: str) -> dict | None:
    """One target-location SOC section row, including unresolved TBA rows."""
    time_indices = [
        index for index, cell in enumerate(cells)
        if _TIME_RE.fullmatch(cell) or cell.strip().upper() == "TBA"
    ]
    for begin_idx in time_indices:
        days = _cell_at(cells, begin_idx, offsets, "days")
        end = _cell_at(cells, begin_idx, offsets, "end")
        if not days or not end or not (_TIME_RE.fullmatch(end) or end.upper() == "TBA"):
            continue
        location = _cell_at(cells, begin_idx, offsets, "location")
        if location is not None and location != teaching_location:
            continue
        section = _cell_at(cells, begin_idx, offsets, "section") or ""
        mini_flag = _cell_at(cells, begin_idx, offsets, "mini") or ""
        unresolved = any(value.strip().upper() == "TBA" for value in (days, cells[begin_idx], end))
        meeting = None if unresolved else {
            "days": days,
            "begin": cells[begin_idx],
            "end": end,
        }
        mini = _section_mini(section, mini_flag)
        if meeting is not None and mini is not None:
            meeting["mini"] = mini
        return {
            "section": section,
            "mini": mini,
            "meeting": meeting,
            "has_unresolved_time": unresolved,
        }
    return None


def _section_records(html: str, teaching_location: str) -> list[dict]:
    """Structured rows from every section table whose rows match teaching_location."""
    records: list[dict] = []
    for table in tables(html):
        offsets = _column_offsets(header_cells(table))
        if offsets is None:
            continue
        for cells in data_rows(table):
            record = _section_record(cells, offsets, teaching_location)
            if record is not None:
                records.append(record)
    return records


def parse_sections(html: str, teaching_location: str) -> dict | None:
    """
    Parse SOC section tables for ``teaching_location``.

    Returns None when the course is not offered there. Otherwise, ``minis``
    identifies its available mini slots and ``section_options`` preserves each
    selectable section schedule instead of flattening alternatives together.
    """
    records = _section_records(html, teaching_location)
    if not records:
        return None
    section_options = build_section_options(records)
    return {
        "minis": sorted({record["mini"] for record in records if record["mini"] is not None}),
        "section_options": section_options,
    }
