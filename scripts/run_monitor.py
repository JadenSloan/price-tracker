"""Entry point for deal monitor.

One-shot pass over the listings currently in the database: for each active
listing, find comparable sold listings, estimate market value, score it as a
deal, and print anything that passes the hard filters. The 5-minute polling
loop described in Architecture.md can wrap around this later.

Every active listing's outcome (not just passing ones) is persisted to
listing_evaluations/comparable_matches each run, so "why didn't this listing
match" is queryable via sqlite3 afterward instead of only visible in stdout.
"""

from datetime import datetime, timezone

from src.analysis.comparable_search import get_sold_comparables
from src.analysis.evaluation import evaluate_deal
from src.analysis.pricing import estimate_market_value
from src.models import DealCriteria
from src.monitor import poller
from src.storage import repository as repo

# Live: search Grailed's actual sold-listing inventory per active listing.
# (Dev-time stand-in was repo.search_sold_candidates against the local DB —
# swap back to that if you want to test against local seed data instead.)
SOLD_SEARCH_FN = poller.search_sold_listings


def main() -> None:
    active_listings = repo.get_active_listings()
    criteria = DealCriteria()
    run_at = datetime.now(timezone.utc).isoformat()

    print(f"Evaluating {len(active_listings)} active listings against per-listing sold comparables...\n")

    deals_found = 0
    for listing in active_listings:
        listing_id = listing["listing_id"]
        sold_comparables = get_sold_comparables(listing, search_fn=SOLD_SEARCH_FN)
        candidate_count = len(sold_comparables)

        valuation = None
        score = None
        discount_pct = None
        fail_reasons = ["no_candidates"]

        if sold_comparables:
            valuation = estimate_market_value(listing, sold_comparables, threshold=criteria.title_similarity_threshold)
            if valuation.estimated_value is None:
                fail_reasons = ["no_comparables_above_threshold"]
            else:
                discount_pct = (valuation.estimated_value - listing["price"]) / valuation.estimated_value
                score = evaluate_deal(listing, valuation, criteria)
                fail_reasons = list(score.fail_reasons)

        repo.save_listing_evaluation(
            active_listing_id=listing_id,
            run_at=run_at,
            candidate_count=candidate_count,
            comparable_count=len(valuation.comparables) if valuation else 0,
            estimated_value=valuation.estimated_value if valuation else None,
            confidence=valuation.confidence if valuation else None,
            discount_pct=discount_pct,
            composite_score=score.composite_score if score else None,
            passes_hard_filters=bool(score and score.passes_hard_filters),
            fail_reasons=fail_reasons,
        )
        if valuation and valuation.comparables:
            repo.save_comparable_matches(listing_id, run_at, valuation.comparables)

        if not (score and score.passes_hard_filters):
            continue

        deals_found += 1
        repo.save_deal({
            **listing,
            "market_value": valuation.estimated_value,
            "discount_pct": discount_pct,
            "deal_score": score.composite_score,
            "detected_at": run_at,
        })

        print(f"DEAL: {listing['title']}")
        print(f"  Ask: ${listing['price']}  Market: ${valuation.estimated_value:.0f}  Discount: {discount_pct:.0%}")
        print(f"  Composite score: {score.composite_score}  Confidence: {valuation.confidence}")
        print(f"  Comparables used: {len(valuation.comparables)}")
        print(f"  {listing['listing_url']}\n")

    print(f"Done. {deals_found} deal(s) found out of {len(active_listings)} active listings.")
    print("Deals are saved in the detected_deals table: sqlite3 listings.db \"SELECT title, price, market_value, discount_pct, deal_score, listing_url FROM detected_deals ORDER BY deal_score DESC;\"")
    print(f"Full per-listing breakdown: sqlite3 listings.db \"SELECT * FROM listing_evaluations WHERE run_at = '{run_at}';\"")


if __name__ == "__main__":
    main()
