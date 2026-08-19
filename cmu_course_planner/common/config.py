SUPPORTED_TEACHING_LOCATION = "Pittsburgh, Pennsylvania"
USER_TO_SOC = {"F": "F", "S": "S", "Su": "M"}
SEM_LABEL = {"F": "Fall", "S": "Spring", "Su": "Summer"}
SOC_SEM_LABEL = {"F": "Fall", "M": "Summer", "S": "Spring"}


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
