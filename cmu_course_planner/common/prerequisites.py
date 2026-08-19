import re
from collections.abc import Collection
from typing import Literal

PrerequisiteStatus = Literal["none", "unknown", "satisfied", "unsatisfied"]

_TOKEN_RE = re.compile(r"\d+|and|or|\(|\)", re.IGNORECASE)


def _course_key(course_id: str) -> str:
    return re.sub(r"\D", "", course_id)


def prerequisite_status(
    prerequisites: str,
    completed_courses: Collection[str],
) -> PrerequisiteStatus:
    text = prerequisites.strip() if prerequisites else "Unknown"
    if text.lower() == "none":
        return "none"
    if text.lower() == "unknown":
        return "unknown"

    tokens = _TOKEN_RE.findall(text)
    if "".join(tokens).lower() != re.sub(r"\s", "", text).lower():
        return "unknown"

    completed = {_course_key(course_id) for course_id in completed_courses}
    position = 0

    def parse_primary() -> bool:
        nonlocal position
        if position >= len(tokens):
            raise ValueError
        token = tokens[position].lower()
        position += 1
        if token == "(":
            value = parse_or()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError
            position += 1
            return value
        if token.isdigit():
            return token in completed
        raise ValueError

    def parse_and() -> bool:
        nonlocal position
        value = parse_primary()
        while position < len(tokens) and tokens[position].lower() == "and":
            position += 1
            next_value = parse_primary()
            value = value and next_value
        return value

    def parse_or() -> bool:
        nonlocal position
        value = parse_and()
        while position < len(tokens) and tokens[position].lower() == "or":
            position += 1
            next_value = parse_and()
            value = value or next_value
        return value

    try:
        satisfied = parse_or()
        if position != len(tokens):
            return "unknown"
    except ValueError:
        return "unknown"
    return "satisfied" if satisfied else "unsatisfied"
