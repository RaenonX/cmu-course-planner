SUPPORTED_TEACHING_LOCATION = "Pittsburgh, Pennsylvania"
USER_TO_SOC = {"F": "F", "S": "S", "Su": "M"}
SEM_LABEL = {"F": "Fall", "S": "Spring", "Su": "Summer"}
SOC_SEM_LABEL = {"F": "Fall", "M": "Summer", "S": "Spring"}


def normalize_course_id(value: str) -> str:
    compact = value.strip().replace("-", "")
    if len(compact) != 5 or not compact.isdigit():
        raise ValueError(f"Invalid course code {value!r}; use five digits such as 17614.")
    return f"{compact[:2]}-{compact[2:]}"


def feasible_course_ids(cfg: dict) -> list[str]:
    section = cfg.get("feasible_schedule") or {}
    values = [*(section.get("core_courses") or []), *(section.get("elective_courses") or [])]
    if not all(isinstance(value, str) for value in values):
        raise ValueError("feasible_schedule course lists must contain course-code strings only.")
    return list(dict.fromkeys(normalize_course_id(value) for value in values))


def validate_teaching_location(value: str | None) -> str:
    if value != SUPPORTED_TEACHING_LOCATION:
        raise ValueError(
            f"Unsupported teaching_location {value!r}. "
            f"Only {SUPPORTED_TEACHING_LOCATION!r} is supported for now."
        )
    return value


def completed_courses_from_config(cfg: dict) -> list[str]:
    courses = cfg.get("completed_courses") or []
    if not isinstance(courses, list) or not all(isinstance(course, str) for course in courses):
        raise ValueError("completed_courses must be a list of course IDs.")
    return courses
