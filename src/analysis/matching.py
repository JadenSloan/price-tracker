"""Text similarity and comparable matching logic."""

import re
from difflib import SequenceMatcher

from src.models import MarketComparable

JACCARD_WEIGHT = 0.6
SEQUENCE_WEIGHT = 0.4
DEFAULT_THRESHOLD = 0.6

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_title(title: str) -> str:
    return title.lower().strip()


def tokenize(title: str) -> set:
    return set(_TOKEN_RE.findall(normalize_title(title)))


def jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a and not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0


def sequence_similarity(title_a: str, title_b: str) -> float:
    return SequenceMatcher(None, normalize_title(title_a), normalize_title(title_b)).ratio()


def title_similarity(title_a: str, title_b: str) -> float:
    jaccard = jaccard_similarity(tokenize(title_a), tokenize(title_b))
    sequence = sequence_similarity(title_a, title_b)
    return JACCARD_WEIGHT * jaccard + SEQUENCE_WEIGHT * sequence


def find_comparables(
    active_listing: dict,
    sold_listings: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[MarketComparable]:
    """Score sold listings (already category/size-qualified by the search
    step — see src.analysis.comparable_search) against an active listing by
    title similarity, keeping ones >= threshold."""
    title = active_listing.get("title") or ""

    comparables = []
    for sold in sold_listings:
        if not sold.get("sold_price"):
            continue

        score = title_similarity(title, sold.get("title") or "")
        if score < threshold:
            continue

        comparables.append(
            MarketComparable(
                listing_id=sold["listing_id"],
                title=sold["title"],
                sold_price=sold["sold_price"],
                date_sold=sold.get("date_sold"),
                similarity_score=score,
                recency_weight=1.0,
                weight=score,
            )
        )

    return comparables
