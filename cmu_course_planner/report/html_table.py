"""Shared helpers for scraping SOC course-details HTML tables."""

import html as html_lib
import re

_TABLE_RE = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)
_THEAD_RE = re.compile(r'<thead[^>]*>(.*?)</thead>', re.DOTALL | re.IGNORECASE)
_TR_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
_TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
_TH_RE = re.compile(r'<th[^>]*>(.*?)</th>', re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r'<[^>]+>')
_WS_RE = re.compile(r'\s+')


def clean_cell(value: str) -> str:
    """Strip tags, unescape entities, and collapse whitespace in a cell or fragment."""
    value = _TAG_RE.sub(' ', value)
    value = html_lib.unescape(value)
    return _WS_RE.sub(' ', value).strip()


def tables(html: str) -> list[str]:
    """Inner HTML of every <table> in the document."""
    return _TABLE_RE.findall(html)


def header_cells(table: str) -> list[str]:
    """Cleaned <th> text from a table's <thead>, or [] when there is no header."""
    match = _THEAD_RE.search(table)
    if not match:
        return []
    return [clean_cell(cell) for cell in _TH_RE.findall(match.group(1))]


def data_rows(table: str) -> list[list[str]]:
    """Cleaned <td> cells for each <tr> in a table."""
    return [[clean_cell(cell) for cell in _TD_RE.findall(row)] for row in _TR_RE.findall(table)]


def header_index(headers: list[str], *names: str, contains: bool = False) -> int | None:
    """
    Index of the first header matching any of ``names`` (case-insensitive).

    With ``contains=True`` a header matches when it *contains* a name (used for
    the "Teaching Location" column); otherwise the match must be exact.
    """
    targets = [name.lower() for name in names]
    for index, raw_header in enumerate(headers):
        header = raw_header.lower()
        matched = any(target in header for target in targets) if contains else header in targets
        if matched:
            return index
    return None
