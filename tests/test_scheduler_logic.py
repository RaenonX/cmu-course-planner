import unittest
from dataclasses import replace

from cmu_course_planner.common.labels import prereq_info, unresolved_time_badge
from cmu_course_planner.common.prerequisites import prerequisite_status
from cmu_course_planner.report.render import _offering_times
from cmu_course_planner.report.section_parse import parse_sections
from cmu_course_planner.suggest.models import Course, Meeting, Offering, SectionOption
from cmu_course_planner.suggest.render_panel import _semester_heading
from cmu_course_planner.suggest.routes import _schedule_signature
from cmu_course_planner.suggest.scheduler import suggest
from cmu_course_planner.suggest.time import _meeting_days
from cmu_course_planner.suggest.units import candidate_slots, semester_unit_total


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
    def test_one_course_in_each_mini_adds_to_twelve_units(self) -> None:
        selected = [
            replace(course("m1-a", 6, [1]), selected_mini=1),
            replace(course("m2-a", 6, [2]), selected_mini=2),
        ]
        self.assertEqual(semester_unit_total(selected), 12)

    def test_same_mini_cannot_be_used_twice(self) -> None:
        selected = replace(course("m1-a", 6, [1]), selected_mini=1)
        self.assertEqual(candidate_slots(course("m1-b", 6, [1]), 12, "F", [selected]), [])
        self.assertEqual(candidate_slots(course("m2-a", 6, [2]), 12, "F", [selected]), [2])

    def test_full_semester_course_counts_its_units_once(self) -> None:
        full = course("full", 6, [])
        self.assertEqual(semester_unit_total([full]), 6)

    def test_fifteen_unit_course_requires_a_fifteen_unit_cap(self) -> None:
        fifteen = course("15-unit", 15, [])
        self.assertEqual(candidate_slots(fifteen, 12, "F", []), [])
        self.assertEqual(candidate_slots(fifteen, 15, "F", []), [0])

    def test_scheduler_stacks_one_course_from_each_mini(self) -> None:
        courses = [
            course("m1-a", 6, [1]), course("m1-b", 6, [1], hour=10),
            course("m2-a", 6, [2]),
        ]
        schedule, unplaced = suggest(courses, ["F"], 12, [], [])
        self.assertEqual({c.course for c in schedule[0]}, {"m1-a", "m2-a"})
        self.assertEqual([c.course for c in unplaced], ["m1-b"])

    def test_stacked_minis_are_reported_as_twelve_units(self) -> None:
        selected = [
            replace(course("m1-a", 6, [1]), selected_mini=1),
            replace(course("m2-a", 6, [2]), selected_mini=2),
        ]
        heading = _semester_heading(0, "F", semester_unit_total(selected), 12, selected)
        self.assertIn("12/12 units", heading)


class WarningTests(unittest.TestCase):
    def test_prerequisite_is_marked_unsatisfied(self) -> None:
        self.assertIn("Unsatisfied", prereq_info("21-370"))
        self.assertNotIn("Unsatisfied", prereq_info("None"))

    def test_completed_course_satisfies_an_or_prerequisite(self) -> None:
        status = prerequisite_status("14513 or 15213 or 15513", ["15-213"])
        self.assertEqual(status, "satisfied")
        self.assertIn("Satisfied", prereq_info("14513 or 15213 or 15513", status))

    def test_all_and_groups_must_be_satisfied(self) -> None:
        expression = "(15213 or 15513) and (21240 or 21241)"
        self.assertEqual(prerequisite_status(expression, ["15-213"]), "unsatisfied")
        self.assertEqual(
            prerequisite_status(expression, ["15-213", "21-240"]),
            "satisfied",
        )

    def test_unstructured_prerequisite_is_unknown(self) -> None:
        self.assertEqual(
            prerequisite_status("Permission of instructor", []),
            "unknown",
        )

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
