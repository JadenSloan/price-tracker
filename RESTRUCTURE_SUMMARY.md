# Codebase Status Summary

**Last updated:** July 16, 2026

This originally documented a one-time cleanup (removing an old `scrapers/`/`processing/` layout in favor of the current `analysis/monitor/storage/utils` structure, January 2026). That structure has held up — this doc now tracks what's actually implemented against it, since the original version was already stale (it predated matching, pricing, evaluation, comparable search, and the run-tracking tables entirely).

## Current structure

```
price-tracker/
├── data/
│   ├── active/grailed_listings.json   # Refreshed by src.monitor.poller (paginated, designer-filtered)
│   ├── sold/grailed_sold.json         # Deep sold-listing seed for local dev/test
│   └── config/                        # brand_aliases.yml, category_map.yml — empty, unused
├── src/
│   ├── models.py                      # ✅ Listing, ComparableSearchCriteria, MarketComparable,
│   │                                  #    MarketValuation, DealCriteria, DealScore
│   ├── analysis/
│   │   ├── comparable_search.py       # ✅ Per-listing sold-comp search + DB-backed caching
│   │   ├── matching.py                # ✅ Title-similarity scoring
│   │   ├── pricing.py                 # ✅ Market value estimation (weighted avg + confidence)
│   │   └── evaluation.py              # ✅ Deal scoring + hard filters (with fail-reason breakdown)
│   ├── monitor/
│   │   ├── poller.py                  # ✅ Paginated active fetch, live per-listing sold search,
│   │   │                              #    deep sold-seed collector
│   │   ├── detector.py                # ⏳ stub — new-vs-seen listing detection
│   │   ├── alerter.py                 # ⏳ stub — Discord/Telegram alerts
│   │   └── scheduler.py               # ⏳ stub — recurring polling loop
│   ├── storage/
│   │   ├── repository.py              # ✅ Full SQLite repository, incl. run-tracking tables
│   │   └── exporters.py               # ⏳ stub — export deals to JSON
│   └── utils/
│       ├── text.py                    # ✅ clean_title() for search queries
│       ├── time.py                    # ✅ listing-age helpers
│       ├── stats.py                   # ⏳ empty
│       └── images.py                  # ⏳ empty
├── scripts/
│   ├── backfill_sold.py               # ✅ Load JSON into listings.db
│   ├── run_monitor.py                 # ✅ One-shot evaluation pass, live search by default
│   └── test_db.py                     # ✅ Manual DB sanity check
└── listings.db                        # SQLite: active_listings, sold_listings,
                                        #   sold_comparable_cache, listing_evaluations,
                                        #   comparable_matches, detected_deals, price_history
```

## What works end-to-end

1. **Data collection** (`monitor/poller.py`): paginated Grailed search using the real `designers=["Chrome Hearts"]` filter (not free-text search) plus server-side category filtering — pulls hundreds to thousands of listings per side instead of one ~40-item page.
2. **Per-listing comparable search** (`analysis/comparable_search.py`): for each active listing, cleans its title and searches sold listings specifically for that item (category via search-side filtering, size via a local post-filter), with a 5-minute cache to avoid redundant live lookups.
3. **Valuation + scoring** (`analysis/matching.py`, `pricing.py`, `evaluation.py`): title-similarity-weighted market value estimate, composite deal score, and hard-filter pass/fail with a specific failure reason per listing (`discount`, `age`, `seller_rating`, `buynow`, `makeoffer`, `transactions`, `no_candidates`, `no_comparables_above_threshold`).
4. **Full run tracking**: every `run_monitor.py` pass persists every active listing's outcome (`listing_evaluations`), the sold listings that matched it (`comparable_matches`), and any deals found (`detected_deals`) — queryable via sqlite3 without re-deriving anything by hand.

## What's still a stub

- **`monitor/scheduler.py`**: no recurring loop yet — `run_monitor.py` is a one-shot pass you re-run manually.
- **`monitor/detector.py`**: every run re-evaluates all active listings; nothing tracks "have I already alerted on this one."
- **`monitor/alerter.py`**: results land in stdout + `detected_deals`, no push notification (Discord/Telegram) yet.
- **`storage/exporters.py`, `utils/stats.py`, `utils/images.py`**: untouched placeholders.
- **Size filtering isn't server-side**: Grailed's per-category size enums need a validated string→enum mapping we don't have yet (see `poller.py::CATEGORY_ENUM_MAP` for the category-side equivalent that *is* done).

See [TODO.md](TODO.md) for the actionable list.
