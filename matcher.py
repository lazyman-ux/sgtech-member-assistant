"""Explainable matching engine for the SGTech Member Community Assistant.

Design goals:
  * Run fully offline, no API keys or external services (hackathon constraint).
  * Every match carries a human-readable "why this match" explanation.
  * Understand a plain-language need by tokenising + synonym expansion against
    the structured fields (expertise, sector, country) in the directory.

This is deliberately a transparent keyword/token scorer rather than an opaque
embedding model so judges and users can see *why* each result was returned.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Synonym / intent expansion.
# Maps words a member might type to the controlled vocabulary used in the CRM
# fields (AreaOfExpertise / BusinessSector / CountriesWithPresence).
# ---------------------------------------------------------------------------
SYNONYMS: Dict[str, List[str]] = {
    # expertise
    "ai": ["artificial intelligence", "machine learning"],
    "a.i.": ["artificial intelligence", "machine learning"],
    "ml": ["machine learning", "artificial intelligence"],
    "genai": ["artificial intelligence", "machine learning"],
    "llm": ["artificial intelligence", "machine learning"],
    "cyber": ["cybersecurity", "security"],
    "cybersec": ["cybersecurity", "security"],
    "security": ["cybersecurity", "security"],
    "infosec": ["cybersecurity", "security"],
    "cloud": ["cloud", "it services"],
    "data": ["data analytics", "data"],
    "analytics": ["data analytics"],
    "fintech": ["fintech", "financial services"],
    "finance": ["fintech", "financial services"],
    "banking": ["fintech", "financial services"],
    "payments": ["fintech", "financial services"],
    "blockchain": ["blockchain"],
    "crypto": ["blockchain"],
    "web3": ["blockchain"],
    "iot": ["iot"],
    "robot": ["robotics"],
    "robotics": ["robotics"],
    "ar": ["augmented/ virtual reality/ metaverse"],
    "vr": ["augmented/ virtual reality/ metaverse"],
    "metaverse": ["augmented/ virtual reality/ metaverse"],
    "mobile": ["mobile applications"],
    "app": ["mobile applications", "software"],
    "apps": ["mobile applications", "software"],
    "software": ["software", "it services"],
    "saas": ["software", "it services"],
    "hardware": ["hardware"],
    "telco": ["telecommunications"],
    "telecom": ["telecommunications"],
    "telecommunications": ["telecommunications"],
    "marketing": ["marketing & media communications"],
    "media": ["marketing & media communications", "ict & media"],
    "consultancy": ["consultancy"],
    "consulting": ["consultancy"],
    "consultant": ["consultancy"],
    "it": ["it services"],
    # sectors
    "healthcare": ["healthcare"],
    "health": ["healthcare"],
    "medical": ["healthcare"],
    "education": ["education"],
    "edtech": ["education"],
    "logistics": ["logistics"],
    "supply": ["logistics"],
    "manufacturing": ["manufacturing"],
    "retail": ["retail"],
    "ecommerce": ["retail", "wholesale trade"],
    "government": ["government"],
    "govtech": ["government"],
    "energy": ["energy & chemicals"],
    "aerospace": ["aerospace"],
    "defence": ["defence"],
    "defense": ["defence"],
    "marine": ["marine & offshore"],
    "realestate": ["real estate"],
    "property": ["real estate"],
    "transport": ["land transport", "sea transport", "air transport"],
    # countries / regions
    "singapore": ["singapore"],
    "sg": ["singapore"],
    "malaysia": ["malaysia"],
    "indonesia": ["indonesia"],
    "vietnam": ["vietnam"],
    "thailand": ["thailand"],
    "philippines": ["philippines"],
    "india": ["india"],
    "china": ["china"],
    "japan": ["japan"],
    "usa": ["united states", "usa"],
    "us": ["united states", "usa"],
    "uk": ["united kingdom"],
    "australia": ["australia"],
    "apac": ["singapore", "malaysia", "indonesia", "thailand", "vietnam"],
    "asean": ["singapore", "malaysia", "indonesia", "thailand", "vietnam", "philippines"],
    "regional": ["malaysia", "indonesia", "thailand", "vietnam"],
}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "clients",
    "company", "companies", "customer", "customers", "find", "firm", "firms",
    "for", "from", "help", "i", "in", "is", "it", "looking", "me", "my",
    "need", "of", "on", "or", "our", "partner", "partners", "please", "provider",
    "providers", "that", "the", "their", "them", "to", "want", "we", "who",
    "with", "working", "work", "would", "you", "your", "want", "someone",
    "some", "any", "get", "show", "list",
}

# Field weights — expertise is the strongest signal, then sector, then geography.
WEIGHT_EXPERTISE = 3.0
WEIGHT_SECTOR = 2.0
WEIGHT_COUNTRY = 1.0
WEIGHT_NAME = 1.5


def _tokenise(text: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def expand_query(need: str) -> List[str]:
    """Turn a plain-language need into a list of controlled-vocabulary terms."""
    tokens = _tokenise(need)
    terms: List[str] = []
    # single-word synonym expansion
    for tok in tokens:
        if tok in STOPWORDS:
            continue
        if tok in SYNONYMS:
            terms.extend(SYNONYMS[tok])
        else:
            terms.append(tok)
    # also keep informative raw tokens so niche words still match the blob
    terms.extend(t for t in tokens if t not in STOPWORDS and len(t) > 2)
    # de-dupe preserving order
    seen = set()
    out = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _field_hits(terms: List[str], values: List[str]) -> List[str]:
    """Return the field values that match any query term."""
    hits = []
    vlow = [(v, v.lower()) for v in values]
    for term in terms:
        for original, low in vlow:
            if term in low or low in term:
                if original not in hits:
                    hits.append(original)
    return hits


def score_member(terms: List[str], member: Dict) -> Tuple[float, str]:
    """Score one member against the expanded query; return (score, reason)."""
    exp_hits = _field_hits(terms, member["expertise"])
    sec_hits = _field_hits(terms, member["sectors"])
    cty_hits = _field_hits(terms, member["countries"])

    name_hit = any(term in member["name"].lower() for term in terms if len(term) > 3)

    score = (
        WEIGHT_EXPERTISE * len(exp_hits)
        + WEIGHT_SECTOR * len(sec_hits)
        + WEIGHT_COUNTRY * len(cty_hits)
        + (WEIGHT_NAME if name_hit else 0.0)
    )

    # Build an explanation.
    reasons = []
    if exp_hits:
        reasons.append("expertise in " + ", ".join(exp_hits[:3]))
    if sec_hits:
        reasons.append("serves the " + ", ".join(sec_hits[:3]) + " sector")
    if cty_hits:
        reasons.append("present in " + ", ".join(cty_hits[:3]))
    if name_hit and not reasons:
        reasons.append("name matches your search")
    reason = "Matches on " + "; ".join(reasons) if reasons else "Loose keyword match"
    return score, reason


def find_partners(
    need: str, members: List[Dict], exclude_id: int | None = None, top_n: int = 5
) -> Tuple[List[Dict], List[str]]:
    """Return the top-N matching members (each with score + reason) and the
    expanded query terms (so the UI can show how the need was interpreted)."""
    terms = expand_query(need)
    scored = []
    for m in members:
        if exclude_id is not None and m["id"] == exclude_id:
            continue
        if not m.get("discoverable", True):
            continue
        score, reason = score_member(terms, m)
        if score > 0:
            scored.append({"member": m, "score": round(score, 1), "reason": reason})
    scored.sort(key=lambda x: (-x["score"], x["member"]["name"]))
    return scored[:top_n], terms


# ---------------------------------------------------------------------------
# Contribution / sponsorship matching.
# ---------------------------------------------------------------------------
def find_contributions(
    member: Dict, opportunities: List[Dict], top_n: int = 3
) -> List[Dict]:
    """Match a member's profile to chapters / sponsorship opportunities."""
    profile_terms = set()
    for field in ("expertise", "sectors", "chapters"):
        for v in member.get(field, []):
            profile_terms.update(_tokenise(v))
    profile_terms -= STOPWORDS

    scored = []
    for opp in opportunities:
        tags = [t.lower() for t in opp.get("tags", [])]
        tag_tokens = set()
        for t in tags:
            tag_tokens.update(_tokenise(t))
        overlap = profile_terms & tag_tokens
        score = len(overlap)

        # Bonus: member already belongs to this chapter -> natural place to step up.
        already_member = any(
            opp.get("name", "") in ch or ch in opp.get("name", "")
            for ch in member.get("chapters", [])
        )
        if already_member:
            score += 1

        matched_tags = [t for t in opp.get("tags", []) if _tokenise(t) and set(_tokenise(t)) & profile_terms]
        reason_bits = []
        if matched_tags:
            reason_bits.append("fits your " + ", ".join(matched_tags[:3]) + " profile")
        if already_member:
            reason_bits.append("you're already in this chapter")
        reason = "Suggested because it " + " and ".join(reason_bits) if reason_bits else \
            "A good general way to raise your profile in the community"

        scored.append({"opportunity": opp, "score": score, "reason": reason})

    scored.sort(key=lambda x: (-x["score"], x["opportunity"]["name"]))
    return scored[:top_n]


def draft_meeting_message(requester: Dict, target: Dict, need: str) -> str:
    """AI-style drafted, personalised meeting/collab request (template-based so it
    runs offline). The member reviews/edits this before sending."""
    their_focus = ", ".join(target.get("expertise", [])[:2]) or "your work"
    our_focus = ", ".join(requester.get("expertise", [])[:2]) or "our work"
    return (
        f"Hi {target['name']} team,\n\n"
        f"I'm reaching out through the SGTech member community. We're "
        f"{requester['name']}, working in {our_focus}. "
        f"I came across your company while looking for \"{need.strip()}\" and your "
        f"focus on {their_focus} looks like a strong fit.\n\n"
        f"Would you be open to a short 20-minute intro call in the next couple of "
        f"weeks to explore whether there's a way we could collaborate?\n\n"
        f"(Our SGTech chapter manager is copied for visibility.)\n\n"
        f"Best regards,\n{requester['name']}"
    )
