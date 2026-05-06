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
