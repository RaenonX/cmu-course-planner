import unittest

from cmu_course_planner.report.section_parse import parse_sections
from cmu_course_planner.suggest.models import Course, Meeting, Offering, SectionOption
from cmu_course_planner.suggest.scheduler import suggest
from cmu_course_planner.suggest.time import _selected_section_option


LOCATION = "Pittsburgh, Pennsylvania"


def section_table(rows: str) -> str:
    return f"""
    <table><thead><tr><th>Section</th><th>Mini</th><th>Days</th><th>Begin</th>
    <th>End</th><th>Teaching Location</th></tr></thead><tbody>{rows}</tbody></table>
    """


def row(section: str, days: str, begin: str, end: str, mini: str = "") -> str:
    return (
        f"<tr><td>{section}</td><td>{mini}</td><td>{days}</td><td>{begin}</td>"
        f"<td>{end}</td><td>{LOCATION}</td></tr>"
    )


class SectionOptionParsingTests(unittest.TestCase):
    def test_primary_sections_are_alternatives(self) -> None:
        parsed = parse_sections(section_table(
            row("A", "M", "9:00AM", "9:50AM")
            + row("B", "T", "10:00AM", "10:50AM")
        ), LOCATION)

        self.assertEqual([option["label"] for option in parsed["section_options"]], ["A", "B"])
        self.assertEqual([len(option["meetings"]) for option in parsed["section_options"]], [1, 1])

    def test_lecture_is_combined_with_each_alternative_section(self) -> None:
        parsed = parse_sections(section_table(
            row("Lec 1", "MW", "9:00AM", "9:50AM")
            + row("A", "F", "10:00AM", "10:50AM")
            + row("B", "F", "11:00AM", "11:50AM")
        ), LOCATION)

        self.assertEqual(
            [option["label"] for option in parsed["section_options"]],
            ["Lec 1 + A", "Lec 1 + B"],
        )
        self.assertEqual([len(option["meetings"]) for option in parsed["section_options"]], [2, 2])

    def test_alternative_matching_lecture_time_is_not_made_required(self) -> None:
        parsed = parse_sections(section_table(
            row("Lec 1", "MW", "9:00AM", "9:50AM")
            + row("A", "F", "9:00AM", "9:50AM")
            + row("B", "MWF", "9:00AM", "9:50AM")
        ), LOCATION)

        self.assertEqual(
            [option["label"] for option in parsed["section_options"]],
            ["Lec 1 + A", "Lec 1 + B"],
        )
        self.assertEqual(
            [option["meetings"][0]["days"] for option in parsed["section_options"]],
            ["MWF", "MWF"],
        )

    def test_repeated_rows_for_one_section_are_all_required(self) -> None:
        parsed = parse_sections(section_table(
            row("A", "MW", "9:00AM", "9:50AM")
            + row("A", "F", "10:00AM", "10:50AM")
        ), LOCATION)

        self.assertEqual(len(parsed["section_options"]), 1)
        self.assertEqual(len(parsed["section_options"][0]["meetings"]), 2)

    def test_equivalent_alternatives_are_merged(self) -> None:
        parsed = parse_sections(section_table(
            row("A", "MW", "9:00AM", "9:50AM")
            + row("B", "MW", "9:00AM", "9:50AM")
        ), LOCATION)

        self.assertEqual([option["label"] for option in parsed["section_options"]], ["A / B"])

    def test_mini_sections_remain_separate_choices(self) -> None:
        parsed = parse_sections(section_table(
            row("A1", "MW", "9:00AM", "9:50AM", "Y")
            + row("B2", "MW", "9:00AM", "9:50AM", "Y")
        ), LOCATION)

        self.assertEqual(parsed["minis"], [1, 2])
        self.assertEqual(
            [(option["label"], option["mini"]) for option in parsed["section_options"]],
            [("A1", 1), ("B2", 2)],
        )


class SectionOptionSchedulingTests(unittest.TestCase):
    def test_scheduler_selects_a_non_conflicting_alternative(self) -> None:
        candidate = Course(
            course="05-391",
            title="Designing Human Centered Software",
            units=12,
            prerequisites="None",
            category=[],
            rating=3,
            rating_by_category={},
            offered_in=[Offering(
                semester="F26",
                minis=[],
                section_options=[
                    SectionOption("A", [Meeting("M", "9:00AM", "9:50AM")]),
                    SectionOption("B", [Meeting("M", "10:00AM", "10:50AM")]),
                ],
                link="https://example.test",
            )],
        )

        schedule, unplaced = suggest(
            [candidate],
            ["F"],
            12,
            [],
            [Meeting("M", "9:00AM", "9:50AM")],
        )

        self.assertEqual(schedule[0][0].selected_section, "B")
        self.assertEqual(unplaced, [])

    def test_same_section_label_is_resolved_in_the_selected_mini(self) -> None:
        candidate = Course(
            course="mini-options",
            title="Mini Options",
            units=6,
            prerequisites="None",
            category=[],
            rating=3,
            rating_by_category={},
            offered_in=[Offering(
                semester="F26",
                minis=[1, 2],
                section_options=[
                    SectionOption("A", [Meeting("M", "9:00AM", "9:50AM", 1)], mini=1),
                    SectionOption("A", [Meeting("T", "10:00AM", "10:50AM", 2)], mini=2),
                ],
                link="https://example.test",
            )],
            selected_mini=2,
            selected_section="A",
        )

        selected = _selected_section_option(candidate, "F")

        self.assertEqual(selected.mini, 2)


if __name__ == "__main__":
    unittest.main()
