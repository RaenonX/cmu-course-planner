import unittest
from dataclasses import replace

from cmu_course_planner.semester_scheduler.enumerate import enumerate_schedules
from cmu_course_planner.degree_planner.models import Course, Meeting, Offering, SectionOption
from cmu_course_planner.degree_planner.scheduler import plan_degree
from cmu_course_planner.degree_planner.units import candidate_slots, mini_workloads


def course(name, units, mini=None, day="M"):
    option = SectionOption(
        "A", [Meeting(day, "9:00AM", "9:50AM", mini)], mini=mini,
    )
    return Course(name, name, units, "None", [], 3, {}, [
        Offering("S27", [mini] if mini else [], [option], ""),
    ])


class MiniWorkloadTests(unittest.TestCase):
    def test_workload_counts_units_even_without_meeting_times(self):
        for soc, first, second in [("F", 1, 2), ("S", 3, 4), ("M", 5, 6)]:
            self.assertEqual(
                mini_workloads([(39, None), (12, first), (9, second)], soc),
                {first: 63, second: 57},
            )

    def test_both_engines_allow_63_63_and_63_57_but_reject_75_51(self):
        for second_units in (12, 9, 6):
            with self.subTest(second_units=second_units):
                first_units = 18 if second_units == 6 else 12
                core = replace(course("core", 39, day="F"), fixed_semester=1)
                electives = [course("first", first_units, 3), course("second", second_units, 4)]
                expected = second_units != 6
                schedules = enumerate_schedules([core], electives, "S27", 24)
                self.assertEqual(any(len(s.choices) == 3 for s in schedules), expected)
                for variant in ("Rating First", "Time Continuity First"):
                    schedule, _ = plan_degree([core, *electives], ["S"], [63], [], [], variant)
                    self.assertEqual(len(schedule[0]) == 3, expected)

    def test_multiple_same_mini_courses_fit_and_conflicts_still_reject(self):
        core = replace(course("core", 39, day="F"), fixed_semester=1)
        first = course("first", 6, 3, "M")
        for day, expected in [("T", True), ("M", False)]:
            second = course("second", 6, 3, day)
            schedules = enumerate_schedules([core], [first, second], "S27", 24)
            self.assertEqual(any(len(s.choices) == 3 for s in schedules), expected)
            schedule, _ = plan_degree([core, first, second], ["S"], [63], [], [])
            self.assertEqual(len(schedule[0]) == 3, expected)

    def test_full_term_addition_must_fit_both_halves(self):
        selected = [replace(course("mini", 12, 3), selected_mini=3)]
        self.assertEqual(candidate_slots(course("full", 40), 63, "S", selected), [])
        self.assertEqual(candidate_slots(course("full", 39), 63, "S", selected), [0])

    def test_fixed_courses_cannot_exceed_weekly_cap(self):
        fixed = [replace(course("full", 39), fixed_semester=1),
                 replace(course("mini", 18, 3, "T"), fixed_semester=1)]
        with self.assertRaisesRegex(ValueError, "cannot be placed"):
            plan_degree(fixed, ["S"], [63], [], [])


if __name__ == "__main__":
    unittest.main()
