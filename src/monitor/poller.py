"""Grailed scraper: bulk-fetches active listings, and searches sold listings
on demand per active listing (see src.analysis.comparable_search).

Also provides fetch_all_sold_listings_for_seed(), a deep paginated pull used
to grow the local dev/test dataset in data/sold — separate from the live
per-listing search path used in production.
"""
import json
from pathlib import Path
from dataclasses import asdict
from grailed_api import GrailedAPIClient
from grailed_api.enums.categories import Accessories, Bottoms, Footwear, Outerwear, Tailoring, Tops
from src.models import ComparableSearchCriteria, Listing
from src.utils.time import days_old

# Output paths
ACTIVE_OUTFILE = Path("data/active/grailed_listings.json")
SOLD_SEED_OUTFILE = Path("data/sold/grailed_sold.json")

DESIGNERS = ["Chrome Hearts"]
DEFAULT_HITS_PER_PAGE = 100
DEFAULT_MAX_PAGES = 25  # cap: up to DEFAULT_MAX_PAGES * DEFAULT_HITS_PER_PAGE items

# Grailed's own `category` field on a product is the coarse department string
# (e.g. "accessories"), but find_products()'s `categories` kwarg wants specific
# subcategory enum members. Passing every member of a department's enum class
# filters to "any subcategory in that department" — verified against the live
# API to correctly narrow results to that coarse category.
CATEGORY_ENUM_MAP = {
    "accessories": Accessories,
    "tops": Tops,
    "outerwear": Outerwear,
    "bottoms": Bottoms,
    "footwear": Footwear,
    "tailoring": Tailoring,
}

client = GrailedAPIClient()


def _product_to_listing_dict(product: dict) -> dict:
    user = product.get("user") or {}
    seller_score = user.get("seller_score") or {}
    cover_photo = product.get("cover_photo") or {}

    listing = Listing(
        listing_id=str(product.get("id")),
        title=product.get("title"),
        price=product.get("price"),
        size=product.get("size"),
        listing_url=f"https://www.grailed.com/listings/{product.get('id')}",
        posted_time=product.get("created_at"),
        bumped_time=product.get("bumped_at"),
        seller_name=user.get("username"),
        seller_rating=seller_score.get("rating_average"),
        rating_count=seller_score.get("rating_count"),
        location=product.get("location"),
        designer=product.get("designer_names"),
        condition=product.get("condition"),
        image_url=cover_photo.get("image_url"),
        sold_price=product.get("sold_price", 0),
        transactions=user.get("total_bought_and_sold"),
        category=product.get("category"),
        buynow=product.get("buynow"),
        makeoffer=product.get("makeoffer"),
        sold=product.get("sold", False),
        date_sold=product.get("sold_at"),
    )
    return asdict(listing)


def _paginate(*, sold: bool, on_sale: bool, hits_per_page: int, max_pages: int, **kwargs) -> list[dict]:
    """Page through find_products() until a short page (end of results) or max_pages."""
    rows = []
    for page in range(1, max_pages + 1):
        products = client.find_products(
            sold=sold, on_sale=on_sale, designers=DESIGNERS,
            page=page, hits_per_page=hits_per_page, **kwargs,
        )
        rows.extend(_product_to_listing_dict(p) for p in products)
        if len(products) < hits_per_page:
            break
    return rows


def fetch_active_listings(hits_per_page: int = DEFAULT_HITS_PER_PAGE, max_pages: int = DEFAULT_MAX_PAGES) -> list[dict]:
    """Bulk-fetch active Chrome Hearts listings, paginated across the full result set."""
    return _paginate(sold=False, on_sale=True, hits_per_page=hits_per_page, max_pages=max_pages)


def fetch_all_sold_listings_for_seed(
    hits_per_page: int = DEFAULT_HITS_PER_PAGE, max_pages: int = DEFAULT_MAX_PAGES
) -> list[dict]:
    """Deep paginated pull of sold Chrome Hearts listings, for growing the
    local dev/test dataset in data/sold/grailed_sold.json (seeds sold_listings
    via scripts/backfill_sold.py). Not part of the live per-listing search
    path — see search_sold_listings() for that."""
    return _paginate(sold=True, on_sale=False, hits_per_page=hits_per_page, max_pages=max_pages)


def search_sold_listings(criteria: ComparableSearchCriteria, limit: int = 100) -> list[dict]:
    """Search Grailed sold listings matching the given criteria (title query,
    category, size).

    Live-mode search_fn for src.analysis.comparable_search.get_sold_comparables.
    """
    kwargs = {}
    category_enum = CATEGORY_ENUM_MAP.get(criteria.category.strip().lower()) if criteria.category else None
    if category_enum is not None:
        kwargs["categories"] = list(category_enum)

    products = client.find_products(
        sold=True,
        on_sale=False,
        designers=DESIGNERS,
        query_search=criteria.query,
        hits_per_page=limit,
        page=1,
        **kwargs,
    )

    rows = [_product_to_listing_dict(p) for p in products]

    # Size isn't filtered server-side: Grailed's per-category size enums (e.g.
    # Accessories.sizes.OS vs Tops.sizes.M) need a string->enum mapping we
    # haven't validated yet across all categories, so this stays a local
    # equality filter rather than risk silently mismatching and returning
    # nothing. Category filtering above IS server-side — verified against
    # the live API, so no local re-check needed for it.
    if criteria.size:
        rows = [r for r in rows if (r.get("size") or "").strip().lower() == criteria.size.strip().lower()]

    return rows[:limit]


def main():
    active_listings = fetch_active_listings()
    with open(ACTIVE_OUTFILE, "w", encoding="utf-8") as f:
        json.dump(active_listings, f, indent=2)
        print(f"Saved {len(active_listings)} listings to {ACTIVE_OUTFILE.resolve()}")

    # Deep sold-listing pull for local dev/test seed data (data/sold ->
    # sold_listings via scripts/backfill_sold.py). The live production path
    # searches sold listings per-active-listing via search_sold_listings()
    # instead (see src.analysis.comparable_search.get_sold_comparables).
    sold_listings = fetch_all_sold_listings_for_seed()
    with open(SOLD_SEED_OUTFILE, "w", encoding="utf-8") as f:
        json.dump(sold_listings, f, indent=2)
        print(f"Saved {len(sold_listings)} listings to {SOLD_SEED_OUTFILE.resolve()}")


if __name__ == "__main__":
    main()
