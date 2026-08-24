import yaml

from ..common.paths import SECTION_POLICIES


def section_bundles(course_id: str | None, semester: str | None) -> list[dict] | None:
    if not course_id or not semester:
        return None
    with open(SECTION_POLICIES, encoding="utf-8") as file:
        policies = yaml.safe_load(file) or {}
    bundles = policies.get(semester, {}).get(course_id)
    if bundles is None:
        return None
    for bundle in bundles:
        if not bundle.get("components"):
            raise ValueError(f"Empty section bundle for {course_id} in {semester}.")
        if bundle.get("modality") not in {"in_person", "online"}:
            raise ValueError(f"Invalid section modality for {course_id} in {semester}.")
    return bundles
