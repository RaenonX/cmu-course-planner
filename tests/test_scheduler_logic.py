import unittest
from dataclasses import replace

from cmu_course_planner.common.labels import prereq_info, unresolved_time_badge
from cmu_course_planner.report.render import _offering_times
from cmu_course_planner.report.section_parse import parse_sections
from cmu_course_planner.suggest.models import Course, Meeting, Offering, SectionOption
from cmu_course_planner.suggest.render_panel import _semester_heading
from cmu_course_planner.suggest.routes import _schedule_signature
from cmu_course_planner.suggest.scheduler import suggest
from cmu_course_planner.suggest.time import _meeting_days
from cmu_course_planner.suggest.units import candidate_slots, semester_unit_loads


def course(course_id: str, units: int, minis: list[int], hour: int | None = None) -> Course:
    options = [
        SectionOption(
            label=f"A{mini}",
            meetings=[
                Meeting(days="M", begin=f"{hour or 8 + mini}:00AM", end=f"{hour or 8 + mini}:50AM", mini=mini),
            ],
            mini=mini,
        )
        for mini in minis
    ] or [SectionOption(label="A", meetings=[])]
    return Course(
        course=course_id,
        title=course_id,
        units=units,
        prerequisites="None",
        category=[],
        rating=3,
        rating_by_category={},
        offered_in=[Offering("F26", minis, options, "https://example.test")],
    )


class DayParsingTests(unittest.TestCase):
    def test_thursday_long_name_does_not_add_sunday(self) -> None:
        self.assertEqual(_meeting_days("Thu"), ["R"])
        self.assertEqual(_meeting_days("T Thu"), ["T", "R"])


class MiniUnitTests(unittest.TestCase):
    def test_two_courses_in_each_mini_fill_a_twelve_unit_capacity(self) -> None:
        selected = [
            replace(course("m1-a", 6, [1]), selected_mini=1),
            replace(course("m1-b", 6, [1]), selected_mini=1),
            replace(course("m2-a", 6, [2]), selected_mini=2),
            replace(course("m2-b", 6, [2]), selected_mini=2),
        ]
        self.assertEqual(semester_unit_loads(selected, "F"), {1: 12, 2: 12})

    def test_same_mini_is_allowed_until_that_slot_reaches_capacity(self) -> None:
        selected = replace(course("m1-a", 6, [1]), selected_mini=1)
        loads = semester_unit_loads([selected], "F")
        self.assertEqual(candidate_slots(course("m1-b", 6, [1]), 12, "F", loads), [1])
        self.assertEqual(candidate_slots(course("m1-c", 7, [1]), 12, "F", loads), [])

    def test_full_semester_course_consumes_capacity_in_both_minis(self) -> None:
        full = course("full", 6, [])
        self.assertEqual(semester_unit_loads([full], "F"), {1: 6, 2: 6})

    def test_fifteen_unit_course_requires_a_fifteen_unit_cap(self) -> None:
        fifteen = course("15-unit", 15, [])
        self.assertEqual(candidate_slots(fifteen, 12, "F", {1: 0, 2: 0}), [])
        self.assertEqual(candidate_slots(fifteen, 15, "F", {1: 0, 2: 0}), [0])

    def test_scheduler_can_place_two_courses_in_each_mini(self) -> None:
        courses = [
            course("m1-a", 6, [1]), course("m1-b", 6, [1], hour=10),
            course("m2-a", 6, [2]), course("m2-b", 6, [2], hour=11),
        ]
        schedule, unplaced = suggest(courses, ["F"], 12, [], [])
        self.assertEqual({c.course for c in schedule[0]}, {c.course for c in courses})
        self.assertEqual(unplaced, [])

    def test_unbalanced_minis_are_reported_separately(self) -> None:
        selected = [
            replace(course("m1-a", 6, [1]), selected_mini=1),
            replace(course("m1-b", 6, [1]), selected_mini=1),
        ]
        heading = _semester_heading(0, "F", semester_unit_loads(selected, "F"), 12, selected)
        self.assertIn("M1 12/12 · M2 0/12", heading)


class WarningTests(unittest.TestCase):
    def test_prerequisite_is_marked_unsatisfied(self) -> None:
        self.assertIn("Unsatisfied", prereq_info("21-370"))
        self.assertNotIn("Unsatisfied", prereq_info("None"))

    def test_tba_section_is_retained_as_an_unresolved_offering(self) -> None:
        html = """
        <table><thead><tr><th>Section</th><th>Mini</th><th>Days</th><th>Begin</th>
        <th>End</th><th>Teaching Location</th></tr></thead><tbody><tr>
        <td>A</td><td></td><td>TBA</td><td>TBA</td><td>TBA</td>
        <td>Pittsburgh, Pennsylvania</td></tr></tbody></table>
        """
        parsed = parse_sections(html, "Pittsburgh, Pennsylvania")
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed["section_options"][0]["has_unresolved_time"])
        self.assertEqual(parsed["section_options"][0]["meetings"], [])

    def test_exported_time_label_marks_incomplete_data(self) -> None:
        offering = {
            "section_options": [{
                "label": "A",
                "meetings": [],
                "has_unresolved_time": True,
            }],
        }
        rendered = _offering_times(["F26"], {"F26": offering})
        self.assertIn("TBA / incomplete", rendered)
        self.assertIn("TBA / incomplete", unresolved_time_badge())


class RouteIdentityTests(unittest.TestCase):
    def test_selected_mini_is_part_of_route_identity(self) -> None:
        flexible = course("mini", 6, [1, 2])
        first = _schedule_signature([[replace(flexible, selected_mini=1)]], [])
        second = _schedule_signature([[replace(flexible, selected_mini=2)]], [])
        self.assertNotEqual(first, second)

    def test_selected_section_is_part_of_route_identity(self) -> None:
        flexible = course("sections", 6, [])
        first = _schedule_signature([[replace(flexible, selected_section="A")]], [])
        second = _schedule_signature([[replace(flexible, selected_section="B")]], [])
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
