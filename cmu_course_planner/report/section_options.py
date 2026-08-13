from collections import defaultdict
import re


_DAY_TOKEN_RE = re.compile(r'Thu|Th|Tue|Tu|Sun|Su|[MTWRFSU]', re.IGNORECASE)
_DAY_ALIASES = {
    "TH": "R", "THU": "R", "R": "R",
    "TU": "T", "TUE": "T", "T": "T",
    "SU": "U", "SUN": "U", "U": "U",
}
_DAY_ORDER = "MTWRFSU"


def _meeting_key(meeting: dict) -> tuple:
    return (
        meeting["days"],
        meeting["begin"],
        meeting["end"],
        meeting.get("mini"),
    )


def _meeting_days(value: str) -> set[str]:
    return {
        _DAY_ALIASES.get(token.upper(), token[0].upper())
        for token in _DAY_TOKEN_RE.findall(value)
    }


def _merge_meetings(meetings: list[dict]) -> list[dict]:
    """Deduplicate same-time components and union the days they cover."""
    merged: dict[tuple, dict] = {}
    for meeting in meetings:
        days = _meeting_days(meeting["days"])
        key = (
            meeting["begin"],
            meeting["end"],
            meeting.get("mini"),
            None if days else meeting["days"],
        )
        if key not in merged:
            merged[key] = meeting.copy()
            continue
        all_days = _meeting_days(merged[key]["days"]) | days
        merged[key]["days"] = "".join(day for day in _DAY_ORDER if day in all_days)
    return list(merged.values())


def _merge_equivalent_groups(groups: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for group in groups:
        key = (
            group["mini"],
            tuple(_meeting_key(meeting) for meeting in group["meetings"]),
            group["has_unresolved_time"],
        )
        if key in merged:
            merged[key]["label"] += f' / {group["label"]}'
        else:
            merged[key] = group
    return list(merged.values())


def _section_groups(records: list[dict]) -> list[dict]:
    by_section: dict[tuple[int | None, str], list[dict]] = defaultdict(list)
    for record in records:
        by_section[(record["mini"], record["section"] or "Unspecified")].append(record)

    groups = []
    for (mini, label), section_records in by_section.items():
        meetings = _merge_meetings([
            record["meeting"]
            for record in section_records
            if record.get("meeting") is not None
        ])
        groups.append({
            "label": label,
            "mini": mini,
            "meetings": meetings,
            "has_unresolved_time": any(record["has_unresolved_time"] for record in section_records),
        })
    return groups


def _combine(lecture: dict, section: dict) -> dict:
    return {
        "label": f'{lecture["label"]} + {section["label"]}',
        "mini": lecture["mini"],
        "meetings": _merge_meetings([*lecture["meetings"], *section["meetings"]]),
        "has_unresolved_time": lecture["has_unresolved_time"] or section["has_unresolved_time"],
    }


def build_section_options(records: list[dict]) -> list[dict]:
    """Build valid selectable schedules from SOC lecture/section rows."""
    groups_by_mini: dict[int | None, list[dict]] = defaultdict(list)
    for group in _section_groups(records):
        groups_by_mini[group["mini"]].append(group)

    options = []
    for groups in groups_by_mini.values():
        lectures = _merge_equivalent_groups([
            group for group in groups if group["label"].lower().startswith("lec")
        ])
        sections = _merge_equivalent_groups([
            group for group in groups if not group["label"].lower().startswith("lec")
        ])
        if lectures and sections:
            options.extend(_combine(lecture, section) for lecture in lectures for section in sections)
        else:
            options.extend(lectures or sections)
    return options
