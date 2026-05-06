def _validate_rating(value: object, context: str) -> int:
    if not isinstance(value, int) or not 1 <= value <= 5:
        raise ValueError(f"{context} must be an integer from 1 to 5.")
    return value


def parse_rating(raw_rating: object, course_id: str) -> tuple[int, dict[str, int]]:
    if isinstance(raw_rating, int):
        return _validate_rating(raw_rating, f"{course_id} rating"), {}
    if isinstance(raw_rating, dict):
        if "default" not in raw_rating:
            raise ValueError(f"{course_id} rating mapping must include a default value.")
        default = _validate_rating(raw_rating["default"], f"{course_id} rating.default")
        category_ratings = {
            str(category): _validate_rating(value, f"{course_id} rating.{category}")
            for category, value in raw_rating.items()
            if category != "default"
        }
        return default, category_ratings
    raise ValueError(f"{course_id} rating must be an integer or a mapping with default.")


def star_rating(rating: int) -> str:
    return f"★{rating}"
