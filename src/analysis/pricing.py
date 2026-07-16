"""Market value calculation from comparable listings."""

from datetime import datetime, timezone

from src.analysis.matching import find_comparables
from src.models import MarketComparable, MarketValuation

RECENCY_HALF_LIFE_DAYS = 30
MIN_COMPARABLES_FOR_FULL_CONFIDENCE = 5

# Coarse condition ranking used to penalize comparables in a different condition tier.
CONDITION_RANK = {
    "is_new": 3,
    "is_gently_used": 2,
    "is_used": 1,
}
CONDITION_STEP_PENALTY = 0.15  # weight multiplier lost per condition tier of difference


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def recency_weight(date_sold: str, now: datetime | None = None) -> float:
    sold_at = _parse_date(date_sold)
    if sold_at is None:
        return 0.5  # unknown recency: neither penalize nor favor heavily
    now = now or datetime.now(timezone.utc)
    age_days = max((now - sold_at).total_seconds() / 86400, 0)
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def condition_factor(condition_a: str, condition_b: str) -> float:
    rank_a = CONDITION_RANK.get((condition_a or "").strip().lower())
    rank_b = CONDITION_RANK.get((condition_b or "").strip().lower())
    if rank_a is None or rank_b is None:
        return 1.0  # unknown condition: don't penalize
    steps = abs(rank_a - rank_b)
    return max(1.0 - steps * CONDITION_STEP_PENALTY, 0.0)


def estimate_market_value(
    active_listing: dict,
    sold_listings: list[dict],
    threshold: float = 0.6,
    now: datetime | None = None,
) -> MarketValuation:
    """Estimate market value for an active listing from weighted sold comparables."""
    listing_id = active_listing["listing_id"]
    raw_comparables = find_comparables(active_listing, sold_listings, threshold)

    if not raw_comparables:
        return MarketValuation(listing_id=listing_id, estimated_value=None, confidence=0.0, comparables=())

    sold_by_id = {s["listing_id"]: s for s in sold_listings}

    weighted_comparables = []
    for comp in raw_comparables:
        sold_record = sold_by_id.get(comp.listing_id, {})
        r_weight = recency_weight(comp.date_sold, now)
        c_factor = condition_factor(active_listing.get("condition"), sold_record.get("condition"))
        weight = comp.similarity_score * r_weight * c_factor

        weighted_comparables.append(
            MarketComparable(
                listing_id=comp.listing_id,
                title=comp.title,
                sold_price=comp.sold_price,
                date_sold=comp.date_sold,
                similarity_score=comp.similarity_score,
                recency_weight=r_weight,
                weight=weight,
            )
        )

    total_weight = sum(c.weight for c in weighted_comparables)
    if total_weight <= 0:
        return MarketValuation(listing_id=listing_id, estimated_value=None, confidence=0.0, comparables=tuple(weighted_comparables))

    estimated_value = sum(c.weight * c.sold_price for c in weighted_comparables) / total_weight

    avg_similarity = sum(c.similarity_score for c in weighted_comparables) / len(weighted_comparables)
    count_factor = min(len(weighted_comparables) / MIN_COMPARABLES_FOR_FULL_CONFIDENCE, 1.0)
    confidence = round(count_factor * avg_similarity, 4)

    return MarketValuation(
        listing_id=listing_id,
        estimated_value=round(estimated_value, 2),
        confidence=confidence,
        comparables=tuple(weighted_comparables),
    )
