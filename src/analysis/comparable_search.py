"""Per-active-listing sold-comparable sourcing, with DB-backed caching."""

from datetime import datetime, timezone
from typing import Callable

from src.models import ComparableSearchCriteria
from src.storage import repository as repo
from src.utils.text import clean_title

# Search criteria (title query + category + size) -> sold listing dicts,
# already qualified by category/size — the search_fn owns that filtering
# entirely, so nothing downstream re-filters on it.
# Dev-time stand-in: lambda c: repo.search_sold_candidates(c.query.split(), c.category, c.size)
# Live: src.monitor.poller.search_sold_listings
SoldSearchFn = Callable[[ComparableSearchCriteria], list[dict]]

DEFAULT_CACHE_TTL_SECONDS = 5 * 60  # matches the intended 5-min poll cadence


def get_sold_comparables(
    active_listing: dict,
    search_fn: SoldSearchFn,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    force_refresh: bool = False,
) -> list[dict]:
    """Return sold comparables for an active listing, searching live and
    caching the result if the cache is missing or stale."""
    listing_id = active_listing["listing_id"]

    if not force_refresh and repo.is_comparable_cache_fresh(listing_id, ttl_seconds):
        cached = [repo.get_sold_listing_by_id(sid) for sid in repo.get_cached_comparable_ids(listing_id)]
        return [c for c in cached if c is not None]

    query = clean_title(active_listing.get("title") or "")
    if not query:
        return []

    criteria = ComparableSearchCriteria(
        query=query,
        category=active_listing.get("category") or "",
        size=active_listing.get("size") or "",
    )

    results = search_fn(criteria)
    for sold in results:
        repo.save_sold_listing(sold)

    repo.save_comparable_cache(
        active_listing_id=listing_id,
        sold_listing_ids=[r["listing_id"] for r in results],
        query=query,
        cached_at=datetime.now(timezone.utc).isoformat(),
    )
    return results
