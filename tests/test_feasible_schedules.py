import json
from pathlib import Path
import tempfile
import unittest

from cmu_course_planner.feasible.config import parse_feasible_config
from cmu_course_planner.feasible.continuity import schedule_continuity
from cmu_course_planner.feasible.enumerate import enumerate_schedules
from cmu_course_planner.feasible.load import load_exact_courses
from cmu_course_planner.feasible.models import CourseChoice, FeasibleSchedule
from cmu_course_planner.feasible.render import _choice_data, build_html
from cmu_course_planner.suggest.models import Course, Meeting, Offering, SectionOption


def option(label, day, begin, end, *, mini=None, modality="in_person", unresolved=False):
    meetings = [] if unresolved else [Meeting(day, begin, end, mini, section=label)]
    return SectionOption(label, meetings, mini, unresolved, (label,), modality)


def course(course_id, units, options, prerequisite_status="satisfied"):
    return Course(
        course=course_id,
        title=f"Title {course_id}",
        units=units,
        prerequisites="None" if prerequisite_status == "satisfied" else "Permission of instructor",
        category=[],
        rating=1,
        rating_by_category={},
        offered_in=[Offering("F26", [], options, "https://example.test")],
        prerequisite_status=prerequisite_status,
    )


class FeasibleConfigTests(unittest.TestCase):
    def test_course_codes_are_normalized_and_lists_must_be_disjoint(self) -> None:
        parsed = parse_feasible_config({
            "feasible_schedule": {
                "semester": "F26",
                "core_courses": ["17614"],
                "elective_courses": ["18-645"],
                "max_elective_units": 21,
            },
            "current_time_ranges": [
                {"label": "17-614 Formal Methods (Lecture 11)"},
                {"label": "17-614 Formal Methods (Section B1)"},
            ],
        })
        self.assertEqual(parsed.core_courses, ("17-614",))
        self.assertEqual(parsed.current_sections, (("17-614", ("Lec 11", "B1")),))
        with self.assertRaisesRegex(ValueError, "overlap"):
            parse_feasible_config({"feasible_schedule": {
                "semester": "F26",
                "core_courses": ["17614"],
                "elective_courses": ["17-614"],
                "max_elective_units": 21,
            }})

    def test_invalid_and_unoffered_courses_are_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            path.write_text(json.dumps({
                "section_policy_version": 1,
                "semesters_checked": ["F26"],
                "courses": [{
                    "course": "11-785",
                    "title": "Introduction to Deep Learning",
                    "units": 12,
                    "prerequisites": "None",
                    "offered_in": [],
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid course code"):
                load_exact_courses(("99-999",), "F26", [], path)
            with self.assertRaisesRegex(ValueError, "not offered in F26"):
                load_exact_courses(("11-785",), "F26", [], path)


class EnumerationTests(unittest.TestCase):
    def test_no_prerequisite_is_not_an_advisory(self) -> None:
        core = course("17-603", 3, [option("A", "M", "9:00AM", "9:50AM")])
        elective = course("18-645", 3, [option("A", "T", "9:00AM", "9:50AM")])
        schedule = enumerate_schedules([core], [elective], "F26", 3)[0]

        self.assertFalse(schedule.has_prerequisite_advisory)

    def test_core_is_mandatory_and_unit_limit_counts_electives_only(self) -> None:
        core = course("17-603", 30, [option("A", "M", "9:00AM", "9:50AM")])
        first = course("18-645", 12, [option("A", "T", "9:00AM", "9:50AM")])
        second = course("15-640", 12, [option("A", "W", "9:00AM", "9:50AM")])

        schedules = enumerate_schedules([core], [first, second], "F26", 21)

        self.assertEqual(len(schedules), 2)
        self.assertTrue(all(any(choice.course.course == "17-603" for choice in item.choices) for item in schedules))
        self.assertEqual({item.elective_units for item in schedules}, {12})

    def test_core_only_schedule_is_not_returned(self) -> None:
        core = course("17-603", 3, [option("A", "M", "9:00AM", "9:50AM")])

        self.assertEqual(enumerate_schedules([core], [], "F26", 0), [])

    def test_all_distinct_complete_bundles_are_considered(self) -> None:
        formal = course("17-614", 6, [
            option("11 + A1", "M", "9:00AM", "9:50AM", mini=1),
            option("11 + B1", "M", "9:00AM", "9:50AM", mini=1),
            option("41 + D1", "M", "7:00PM", "8:20PM", mini=1, modality="online"),
        ])
        schedules = enumerate_schedules([], [formal], "F26", 12)
        self.assertEqual([item.choices[0].option.label for item in schedules], [
            "11 + A1", "11 + B1", "41 + D1",
        ])

    def test_second_online_course_and_time_conflicts_are_excluded(self) -> None:
        core = course("17-603", 3, [option(
            "D", "M", "7:00PM", "8:20PM", modality="online",
        )])
        online = course("17-623", 6, [option(
            "42 + D2", "T", "7:00PM", "8:20PM", mini=2, modality="online",
        )])
        conflict = course("18-645", 12, [option("A", "M", "7:30PM", "8:30PM")])
        valid = course("15-640", 12, [option("A", "W", "9:00AM", "9:50AM")])

        schedules = enumerate_schedules([core], [online, conflict, valid], "F26", 21)

        self.assertEqual(len(schedules), 1)
        self.assertEqual(
            [choice.course.course for choice in schedules[0].choices],
            ["15-640", "17-603"],
        )

    def test_unknown_time_is_retained_and_marked(self) -> None:
        unknown = course("17-603", 3, [option(
            "A", "", "", "", unresolved=True,
        )], prerequisite_status="unknown")
        elective = course("18-645", 3, [option("A", "T", "9:00AM", "9:50AM")])
        schedules = enumerate_schedules([unknown], [elective], "F26", 3)
        config = parse_feasible_config({"feasible_schedule": {
            "semester": "F26",
            "core_courses": ["17-603"],
            "elective_courses": ["18-645"],
            "max_elective_units": 3,
        }})

        rendered = build_html(config, schedules, "test snapshot")

        self.assertIn("cannot be fully conflict-verified", rendered)
        self.assertIn("Advisory", rendered)
        self.assertIn("TBA / incomplete", rendered)

    def test_continuity_groups_weekdays_and_excludes_transition_minutes(self) -> None:
        core_option = SectionOption("A", [
            Meeting("MW", "8:00AM", "9:00AM", section="A"),
            Meeting("MW", "9:10AM", "10:00AM", section="A"),
        ], components=("A",))
        elective_option = SectionOption("B1", [
            Meeting("TR", "12:30PM", "1:50PM", 1, section="B1"),
            Meeting("TR", "3:20PM", "4:50PM", 1, section="B1"),
        ], mini=1, components=("B1",))
        core = course("17-603", 3, [core_option])
        elective = course("18-645", 12, [elective_option])
        schedule = enumerate_schedules([core], [elective], "F26", 24)[0]

        continuity = schedule_continuity(schedule, "F26")

        self.assertEqual(continuity["totalGapMinutes"], 160)
        self.assertEqual(continuity["maxGapMinutes"], 80)
        self.assertEqual(continuity["minis"][0]["groups"], [
            {"days": ["M", "W"], "beginMinutes": 480, "endMinutes": 600, "gapMinutes": 0},
            {"days": ["T", "R"], "beginMinutes": 750, "endMinutes": 1010, "gapMinutes": 80},
        ])

    def test_identical_component_times_render_as_one_meeting(self) -> None:
        bundled = SectionOption("Lec 1 + M", [
            Meeting("MW", "8:00AM", "9:20AM", section="Lec 1"),
            Meeting("MW", "8:00AM", "9:20AM", section="M"),
        ], components=("Lec 1", "M"))
        deep_learning = course("11-785", 12, [bundled])

        choice_data = _choice_data(CourseChoice(deep_learning, bundled, False))

        self.assertEqual(len(choice_data["meetings"]), 1)
        self.assertEqual(choice_data["meetings"][0]["section"], "Lec 1 + M")

    def test_export_uses_elective_terms_tree_selection_and_online_text(self) -> None:
        core = course("17-603", 3, [option("D", "M", "7:00PM", "8:20PM", modality="online")])
        elective = course("18-645", 12, [option("A", "T", "9:00AM", "9:50AM")])
        schedules = enumerate_schedules([core], [elective], "F26", 12)
        config = parse_feasible_config({"feasible_schedule": {
            "semester": "F26",
            "core_courses": ["17-603"],
            "elective_courses": ["18-645"],
            "max_elective_units": 12,
        }})

        rendered = build_html(config, schedules, "test snapshot")

        self.assertIn("schedule-tree", rendered)
        self.assertNotIn("schedule-select", rendered)
        self.assertIn('"role":"Elective"', rendered)
        self.assertIn('"electiveUnits":12', rendered)
        self.assertIn('"online":true', rendered)
        self.assertIn("is-online", rendered)
        self.assertIn('leaf.classList.add("has-online")', rendered)
        self.assertIn(".schedule-leaf.has-online .schedule-entry-metrics", rendered)
        self.assertIn("Sky blue</span> = online.", rendered)
        self.assertIn('"totalGapMinutes":0', rendered)
        self.assertIn('"maxGapMinutes":0', rendered)
        self.assertIn("Gap: Total", rendered)
        self.assertIn("· Max", rendered)
        self.assertIn("course-popover", rendered)
        self.assertIn("Section swaps needed", rendered)
        self.assertIn("sameComponents(current, choice.components)", rendered)
        self.assertIn("schedule-entry-metrics", rendered)
        self.assertIn("left.swapCount - right.swapCount", rendered)
        self.assertLess(
            rendered.index("left.swapCount - right.swapCount"),
            rendered.index("left.schedule.totalGapMinutes - right.schedule.totalGapMinutes"),
        )
        self.assertIn('leaf.addEventListener("click", selectLeaf)', rendered)
        self.assertIn('leaf.setAttribute("aria-selected", "false")', rendered)
        self.assertIn("Exact course section", rendered)
        self.assertIn("All sections", rendered)
        self.assertIn("scheduleMatchesSection", rendered)
        self.assertIn("choice.components.includes(selectedSection.component)", rendered)
        self.assertIn("No feasible schedules match this exact section.", rendered)


if __name__ == "__main__":
    unittest.main()
