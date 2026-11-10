import unittest
from dataclasses import replace
from itertools import product

from cmu_course_planner.degree_planner.models import Course, Meeting, Offering, SectionOption
from client_planner import client_paths, run_client


def course(code, options=None, fixed=None):
    return Course(code, code, 12, "None", [], 3, {},
                  [Offering("F26", [], options or [SectionOption("A", [])], "")],
                  fixed_semester=fixed)


def explicit_paths(paths):
    result = set()
    for schedule in product(*paths["choices"]):
        courses = [c.course for semester in schedule for c in semester]
        if len(courses) != len(set(courses)):
            continue
        result.add(tuple(tuple((c.course, c.selected_section, c.selected_mini)
                               for c in semester) for semester in schedule))
    return result


class ExhaustiveRouteTests(unittest.TestCase):
    def test_every_assignment_matches_independent_brute_force(self):
        courses = [course(code, [SectionOption("A", []), SectionOption("B", [])])
                   for code in ["a", "b", "c"]]
        paths = client_paths(courses, ["F", "F"], [12, 12], [])
        expected = set()
        assignments = [None, (0, "A"), (0, "B"), (1, "A"), (1, "B")]
        for choices in product(assignments, repeat=3):
            schedule = [[], []]
            for item, choice in zip(courses, choices):
                if choice is not None:
                    semester, section = choice
                    schedule[semester].append((item.course, section, None))
            if all(len(semester) <= 1 for semester in schedule):
                expected.add(tuple(tuple(semester) for semester in schedule))
        self.assertEqual(explicit_paths(paths), expected)
        self.assertEqual(paths["count"], len(expected))
        self.assertEqual(paths["count"], 37)

    def test_fixed_sections_are_explored_with_optional_course_conflicts(self):
        fixed = course("fixed", [
            SectionOption("A", [Meeting("M", "9:00AM", "9:50AM")]),
            SectionOption("B", [Meeting("M", "10:00AM", "10:50AM")]),
        ], fixed=1)
        elective = course("elective", [
            SectionOption("A", [Meeting("M", "9:00AM", "9:50AM")]),
        ])
        paths = client_paths([fixed, elective], ["F"], [24], [])
        self.assertEqual(paths["count"], 3)
        self.assertTrue(all(any(c.course == "fixed" for c in term) for term in paths["choices"][0]))
        self.assertTrue(any({(c.course, c.selected_section) for c in term}
                            == {("fixed", "B"), ("elective", "A")}
                            for term in paths["choices"][0]))

    def test_all_sections_survive_without_a_search_limit(self):
        many_sections = course("many", [SectionOption(str(i), []) for i in range(250)])
        paths = client_paths([many_sections], ["F"], [12], [])
        self.assertEqual(paths["count"], 251)
        self.assertEqual({term[0].selected_section for term in paths["choices"][0] if term},
                         {str(i) for i in range(250)})

    def test_mini_choices_are_distinct_and_current_commitments_are_respected(self):
        mini = replace(course("mini"), units=6, offered_in=[Offering("F26", [1, 2], [
            SectionOption("A1", [Meeting("M", "9:00AM", "9:50AM", mini=1)], mini=1),
            SectionOption("A2", [Meeting("M", "9:00AM", "9:50AM", mini=2)], mini=2),
        ], "")])
        paths = client_paths([mini], ["F"], [12], [])
        self.assertEqual(paths["count"], 3)
        paths = client_paths([mini], ["F"], [12],
                                       [Meeting("M", "9:00AM", "9:50AM", mini=1)])
        self.assertEqual(paths["count"], 2)
        self.assertEqual({c.selected_mini for term in paths["choices"][0] for c in term}, {2})

    def test_input_order_does_not_create_duplicate_course_permutations(self):
        courses = [course("a"), course("b")]
        first = client_paths(courses, ["F"], [24], [])
        second = client_paths(list(reversed(courses)), ["F"], [24], [])
        self.assertEqual(first["count"], 4)
        self.assertEqual(explicit_paths(first), explicit_paths(second))

    def test_preferences_count_all_paths_and_conflicting_preferences_return_zero(self):
        courses = [course(code, [SectionOption("A", []), SectionOption("B", [])])
                   for code in ["a", "b", "c"]]
        for required, excluded, expected in [([0], [], 20), ([0], [1], 12), ([0], [0], 0)]:
            result = run_client(courses, ["F", "F"], [12, 12], [],
                                operation="filterCount", required=required, excluded=excluded)
            self.assertEqual(int(result["count"]), expected)

    def test_options_must_match_the_detected_offering_mini_slots(self):
        mini = replace(course("mini"), units=6, offered_in=[Offering("F26", [1], [
            SectionOption("A1", [], mini=1), SectionOption("Unspecified", []),
        ], "")])
        paths = client_paths([mini], ["F"], [12], [])
        self.assertEqual(paths["count"], 2)
        self.assertEqual({c.selected_section for term in paths["choices"][0] for c in term}, {"A1"})


if __name__ == "__main__":
    unittest.main()
