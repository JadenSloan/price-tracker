"""Deal evaluation and scoring logic."""

from datetime import datetime, timezone

from src.models import DealCriteria, DealScore, MarketValuation

DISCOUNT_WEIGHT = 0.50
SELLER_WEIGHT = 0.25
URGENCY_WEIGHT = 0.15
DEMAND_WEIGHT = 0.10

DISCOUNT_CAP = 0.50  # discount_score maxes out at 50% under market
MAX_SCORED_TRANSACTIONS = 50  # transactions beyond this don't add more seller_score
MAX_SCORED_PRICE_DROPS = 3  # price drops beyond this don't add more urgency_score


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def listing_age_days(listing: dict, now: datetime | None = None) -> float | None:
    posted_at = _parse_date(listing.get("posted_time"))
    if posted_at is None:
        return None
    now = now or datetime.now(timezone.utc)
    return (now - posted_at).total_seconds() / 86400


def hard_filter_failures(
    listing: dict, criteria: DealCriteria, discount_pct: float, now: datetime | None = None
) -> tuple[str, ...]:
    """Return the names of every hard filter this listing fails (empty if it passes all)."""
    reasons = []
    if discount_pct < criteria.min_discount_pct:
        reasons.append("discount")
    if criteria.require_buynow and not listing.get("buynow"):
        reasons.append("buynow")
    if criteria.require_makeoffer and not listing.get("makeoffer"):
        reasons.append("makeoffer")
    rating = listing.get("seller_rating")
    if rating is None or rating < criteria.min_seller_rating:
        reasons.append("seller_rating")
    if (listing.get("transactions") or 0) < criteria.min_transactions:
        reasons.append("transactions")
    age = listing_age_days(listing, now)
    if age is not None and age > criteria.max_listing_age_days:
        reasons.append("age")
    return tuple(reasons)


def passes_hard_filters(listing: dict, criteria: DealCriteria, discount_pct: float, now: datetime | None = None) -> bool:
    return not hard_filter_failures(listing, criteria, discount_pct, now)


def discount_score(ask_price: float, market_value: float) -> float:
    if not market_value or market_value <= 0:
        return 0.0
    raw_discount = (market_value - ask_price) / market_value
    return max(min(raw_discount, DISCOUNT_CAP), 0.0) / DISCOUNT_CAP


def seller_score(seller_rating: float | None, transactions: int | None) -> float:
    rating_norm = min(max((seller_rating or 0) / 5.0, 0.0), 1.0)
    transactions_norm = min((transactions or 0) / MAX_SCORED_TRANSACTIONS, 1.0)
    return 0.7 * rating_norm + 0.3 * transactions_norm


def urgency_score(price_drop_count: int = 0) -> float:
    return min(max(price_drop_count, 0) / MAX_SCORED_PRICE_DROPS, 1.0)


def demand_score(heat: float | None = None) -> float:
    # Grailed's API response doesn't expose likes/heat in the fields we currently
    # scrape, so this is neutral until the poller captures that signal.
    if heat is None:
        return 0.5
    return min(max(heat, 0.0), 1.0)


def evaluate_deal(
    listing: dict,
    valuation: MarketValuation,
    criteria: DealCriteria = DealCriteria(),
    price_drop_count: int = 0,
    heat: float | None = None,
    now: datetime | None = None,
) -> DealScore:
    """Score an active listing against its market valuation."""
    ask_price = listing["price"]
    market_value = valuation.estimated_value

    d_score = discount_score(ask_price, market_value) if market_value else 0.0
    s_score = seller_score(listing.get("seller_rating"), listing.get("transactions"))
    u_score = urgency_score(price_drop_count)
    dem_score = demand_score(heat)

    composite = (
        DISCOUNT_WEIGHT * d_score
        + SELLER_WEIGHT * s_score
        + URGENCY_WEIGHT * u_score
        + DEMAND_WEIGHT * dem_score
    ) * valuation.confidence

    raw_discount_pct = (market_value - ask_price) / market_value if market_value else 0.0
    fail_reasons = hard_filter_failures(listing, criteria, raw_discount_pct, now) if market_value is not None else ("no_valuation",)
    passes = market_value is not None and not fail_reasons

    return DealScore(
        listing_id=listing["listing_id"],
        discount_score=round(d_score, 4),
        seller_score=round(s_score, 4),
        urgency_score=round(u_score, 4),
        demand_score=round(dem_score, 4),
        composite_score=round(composite, 4),
        passes_hard_filters=passes,
        fail_reasons=fail_reasons,
    )
