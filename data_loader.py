"""Load and normalise the SGTech member directory from input/members.csv.

The CSV has five columns exported from the CRM:
    Company Name, BusinessSector, AreaOfExpertise, CountriesWithPresence, JoinedChapterName

Most fields are comma-separated multi-value strings. The JoinedChapterName field
is tricky because some chapter names themselves contain commas
(e.g. "AI, Cloud and Data Chapter (AICDC)"), so we split it on the known chapter
catalogue rather than naively on commas.
"""
from __future__ import annotations

import csv
import os
import re
from functools import lru_cache
from typing import List, Dict

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "input", "members.csv")

# Canonical SGTech chapter names (used to safely split JoinedChapterName, which
# contains commas inside individual chapter names).
CHAPTERS = [
    "AI, Cloud and Data Chapter (AICDC)",
    "Cyber Security Chapter (CSC)",
    "Data Centre Chapter (DCC)",
    "Singapore Enterprise Chapter (SEC)",
    "Smart Nation Chapter (SNC)",
    "Digital Transformation Chapter (DxC)",
]


def _split_multi(value: str) -> List[str]:
    """Split a simple comma-separated multi-value cell into clean tokens."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _split_chapters(value: str) -> List[str]:
    """Split JoinedChapterName, respecting chapter names that contain commas."""
    if not value:
        return []
    text = value.strip()
    found: List[str] = []
    # Greedily pull out any known chapter name wherever it appears.
    remaining = text
    for chapter in CHAPTERS:
        if chapter in remaining:
            found.append(chapter)
            remaining = remaining.replace(chapter, " ")
    # Anything left over that still looks like a "Chapter (...)" entry.
    for leftover in re.split(r",", remaining):
        leftover = leftover.strip(" ,")
        if leftover and "Chapter" in leftover:
            found.append(leftover)
    return found


@lru_cache(maxsize=1)
def load_members() -> List[Dict]:
    """Return the member directory as a list of normalised dicts.

    Each member dict has:
        id, name, sectors[], expertise[], countries[], chapters[],
        discoverable (bool), plus a precomputed lowercase `search_blob`.
    """
    members: List[Dict] = []
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"Member directory not found at {CSV_PATH}. "
            "Expected the recovered SGTech members.csv."
        )

    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader):
            name = (row.get("Company Name") or "").strip()
            if not name:
                continue
            sectors = _split_multi(row.get("BusinessSector", ""))
            expertise = _split_multi(row.get("AreaOfExpertise", ""))
            countries = _split_multi(row.get("CountriesWithPresence", ""))
            chapters = _split_chapters(row.get("JoinedChapterName", ""))

            blob = " ".join(
                [name] + sectors + expertise + countries + chapters
            ).lower()

            members.append(
                {
                    "id": idx,
                    "name": name,
                    "sectors": sectors,
                    "expertise": expertise,
                    "countries": countries,
                    "chapters": chapters,
                    # In production only opted-in members are discoverable (PDPA).
                    # Here we model it as a flag; all are discoverable for the demo.
                    "discoverable": True,
                    "search_blob": blob,
                }
            )
    return members


@lru_cache(maxsize=1)
def directory_stats() -> Dict:
    """Headline numbers for the landing page / admin view."""
    members = load_members()
    sectors, expertise, countries, chapters = set(), set(), set(), set()
    for m in members:
        sectors.update(m["sectors"])
        expertise.update(m["expertise"])
        countries.update(m["countries"])
        chapters.update(m["chapters"])
    return {
        "total_members": len(members),
        "distinct_sectors": len(sectors),
        "distinct_expertise": len(expertise),
        "distinct_countries": len(countries),
        "distinct_chapters": len(chapters),
    }


def get_member(member_id: int) -> Dict | None:
    for m in load_members():
        if m["id"] == member_id:
            return m
    return None


def find_member_by_name(name: str) -> Dict | None:
    name_l = name.strip().lower()
    for m in load_members():
        if m["name"].lower() == name_l:
            return m
    return None


if __name__ == "__main__":
    ms = load_members()
    print(f"Loaded {len(ms)} members")
    print("Stats:", directory_stats())
    print("Example:", ms[3])
