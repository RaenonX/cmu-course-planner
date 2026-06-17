import re
import urllib.error
import urllib.request
from datetime import datetime

from ..common.config import SUPPORTED_TEACHING_LOCATION
from .section_parse import parse_sections

SOC_SEARCH = "https://enr-apps.as.cmu.edu/open/SOC/SOCServlet/search"
ENR_BASE = "https://enr-apps.as.cmu.edu/open/SOC/SOCServlet/courseDetails"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SEM_START_MONTH = {"S": 1, "M": 5, "F": 8}

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""

def available_semesters() -> list[str]:
    """Return semester codes from the SOC search page in listing order (newest first)."""
    _, html = fetch(SOC_SEARCH)
    m = re.search(
        r'<select[^>]+name=["\']SEMESTER["\'][^>]*>(.*?)</select>',
        html, re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return []
    return re.findall(r'<option[^>]+value=["\']([^"\']+)["\']', m.group(1), re.IGNORECASE)

def sem_start(code: str) -> datetime:
    return datetime(2000 + int(code[1:]), SEM_START_MONTH[code[0]], 1)

def filter_semesters(codes: list[str], today: datetime, years_back: int) -> list[str]:
    future = [c for c in codes if sem_start(c) > today]
    # Nearest upcoming semester (e.g. F26 when today is May 2026).
    next_sem = min(future, key=sem_start) if future else None

    if next_sem:
        # Anchor the lookback on the next semester: go back `years_back` cycles
        # of the same type (e.g. F26 - 1yr → cutoff = F25 start Aug 2025),
        # so exactly one full cycle is included (S26, M26) without spilling into F25.
        anchor_year = 2000 + int(next_sem[1:]) - years_back
        cutoff = datetime(anchor_year, SEM_START_MONTH[next_sem[0]], 1)
    else:
        cutoff = datetime(today.year - years_back, 1, 1)

    past = [c for c in codes if cutoff < sem_start(c) <= today]
    return ([next_sem] if next_sem else []) + past

def enr_link(course_id: str, sem: str) -> str:
    return f"{ENR_BASE}?COURSE={course_id.replace('-', '')}&SEMESTER={sem}"

def fetch_offering(course_id: str, sem: str, teaching_location: str) -> dict | None:
    """
    Return None if not offered this semester.
    Return {"link": str, "minis": list[int], "meetings": list[dict], "html": str} if offered.
    minis is empty for full-semester courses. html is used to extract title/units.
    """
    url = enr_link(course_id, sem)
    status, body = fetch(url)
    if status != 200 or "Days" not in body or "Begin" not in body:
        return None
    sections = parse_sections(body, teaching_location)
    if sections is None:
        return None
    return {
        "link": url,
        "minis": sections["minis"],
        "meetings": sections["meetings"],
        "html": body,
    }
