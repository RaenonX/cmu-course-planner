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
        meeting.get("section"),
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
            meeting.get("section"),
            None if days else meeting["days"],
        )
        if key not in merged:
            merged[key] = meeting.copy()
            continue
        all_days = _meeting_days(merged[key]["days"]) | days
        merged[key]["days"] = "".join(day for day in _DAY_ORDER if day in all_days)
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
            "components": [label],
            "modality": "in_person",
        })
    return groups


def _combine(lecture: dict, section: dict) -> dict:
    return {
        "label": f'{lecture["label"]} + {section["label"]}',
        "mini": lecture["mini"],
        "meetings": _merge_meetings([*lecture["meetings"], *section["meetings"]]),
        "has_unresolved_time": lecture["has_unresolved_time"] or section["has_unresolved_time"],
        "components": [lecture["label"], section["label"]],
        "modality": "in_person",
    }


def _policy_options(groups: list[dict], bundles: list[dict]) -> list[dict]:
    by_label = {group["label"]: group for group in groups}
    options = []
    for bundle in bundles:
        labels = bundle["components"]
        missing = [label for label in labels if label not in by_label]
        if missing:
            raise ValueError(f"Section policy references missing component(s): {', '.join(missing)}")
        selected = [by_label[label] for label in labels]
        minis = {group["mini"] for group in selected}
        if len(minis) != 1:
            raise ValueError(f"Section policy mixes mini slots: {' + '.join(labels)}")
        options.append({
            "label": " + ".join(labels),
            "mini": next(iter(minis)),
            "meetings": _merge_meetings([
                meeting for group in selected for meeting in group["meetings"]
            ]),
            "has_unresolved_time": any(group["has_unresolved_time"] for group in selected),
            "components": labels,
            "modality": bundle["modality"],
        })
    return options


def build_section_options(records: list[dict], bundles: list[dict] | None = None) -> list[dict]:
    """Build valid selectable schedules from SOC lecture/section rows."""
    groups = _section_groups(records)
    if bundles is not None:
        return _policy_options(groups, bundles)

    groups_by_mini: dict[int | None, list[dict]] = defaultdict(list)
    for group in groups:
        groups_by_mini[group["mini"]].append(group)

    options = []
    for groups in groups_by_mini.values():
        lectures = [
            group for group in groups if group["label"].lower().startswith("lec")
        ]
        sections = [
            group for group in groups if not group["label"].lower().startswith("lec")
        ]
        if lectures and sections:
            options.extend(_combine(lecture, section) for lecture in lectures for section in sections)
        else:
            options.extend(lectures or sections)
    return options
