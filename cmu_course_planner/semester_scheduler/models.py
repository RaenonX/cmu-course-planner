from dataclasses import dataclass, replace

from ..degree_planner.models import Course, SectionOption


@dataclass(frozen=True)
class CourseChoice:
    course: Course
    option: SectionOption
    is_core: bool

    def selected_course(self) -> Course:
        return replace(
            self.course,
            selected_mini=self.option.mini,
            selected_section=self.option.label,
        )


@dataclass(frozen=True)
class SemesterSchedule:
    choices: tuple[CourseChoice, ...]
    elective_units: int

    @property
    def has_unknown_time(self) -> bool:
        return any(choice.option.has_unresolved_time for choice in self.choices)

    @property
    def has_prerequisite_advisory(self) -> bool:
        return any(
            choice.course.prerequisite_status in {"unknown", "unsatisfied"}
            for choice in self.choices
        )
