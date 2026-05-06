from dataclasses import dataclass

@dataclass
class Meeting:
    days: str
    begin: str
    end: str

@dataclass
class Offering:
    semester: str
    minis: list[int]   # empty = full semester; [2] = mini-2 only; [1,2] = either slot
    meetings: list[Meeting]
    link: str

@dataclass
class Course:
    course: str
    title: str
    units: int
    prerequisites: str
    category: list[str]
    rating: int
    rating_by_category: dict[str, int]
    offered_in: list[Offering]   # newest first

    def offered_soc_types(self) -> set[str]:
        return {o.semester[0] for o in self.offered_in}

    def effective_rating(self, prefer: list[str]) -> int:
        category_ratings = [
            self.rating_by_category[category]
            for category in prefer
            if category in self.category and category in self.rating_by_category
        ]
        return max(category_ratings, default=self.rating)

    def offering_for(self, soc_type: str) -> Offering | None:
        return next((o for o in self.offered_in if o.semester[0] == soc_type), None)

    def last_link_for(self, soc_type: str) -> str | None:
        o = self.offering_for(soc_type)
        return o.link if o else None

    def last_link(self) -> str | None:
        return self.offered_in[0].link if self.offered_in else None
