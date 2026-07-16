# Grailed Deal Monitor

Finds underpriced Chrome Hearts listings on Grailed by comparing each active listing's asking price against what similar items have actually sold for, then scoring how good a deal it is.

## How it works

```
1. Active listings   src/monitor/poller.py:fetch_active_listings()
   → paginated search (designers=["Chrome Hearts"]) → data/active/grailed_listings.json

2. Seed the DB        scripts/backfill_sold.py
   → loads active + sold JSON into listings.db (SQLite) via src/storage/repository.py

3. Per-listing comps  src/analysis/comparable_search.py:get_sold_comparables()
   → for each active listing: clean its title (src/utils/text.py) → search sold
     listings for that specific item (category + designer server-side, size
     locally) → cache results in sold_comparable_cache (5 min TTL)

4. Scoring            src/analysis/matching.py + pricing.py
   → matching.find_comparables(): score each candidate by title similarity
     (Jaccard + sequence match), drop anything below threshold (0.6)
   → pricing.estimate_market_value(): weighted average of comparable sold
     prices (recency decay, condition penalty) + a confidence score

5. Deal evaluation     src/analysis/evaluation.py:evaluate_deal()
   → hard filters (ALL must pass): discount ≥30%, buynow+makeoffer both true,
     seller rating ≥3.0, ≥1 transaction, listing age ≤180 days
   → composite score (discount 50% / seller 25% / urgency 15% / demand 10%) × confidence

6. Entry point         scripts/run_monitor.py
   → ties it all together; every listing's outcome (pass or fail, and why) is
     persisted, and passing deals are saved to detected_deals
```

## Setup

```bash
python3 -m venv .venv          # if you don't already have one
source .venv/bin/activate
pip install grailed_api        # only real dependency — an unofficial Grailed API wrapper
```

## Running it

```bash
python3 -m src.monitor.poller       # bulk-fetch active listings + a deep sold-listing seed
                                    # (data/active/grailed_listings.json, data/sold/grailed_sold.json)
python3 -m scripts.backfill_sold    # load that JSON into listings.db
python3 -m scripts.run_monitor      # evaluate every active listing, print + persist deals
python3 -m scripts.test_db          # sanity-check row counts / data integrity in listings.db
```

`run_monitor.py` currently searches sold listings **live** against Grailed per active listing (`SOLD_SEARCH_FN = poller.search_sold_listings` in `scripts/run_monitor.py`). To test against the local seed data instead (no network calls, useful for quick iteration), swap that line for:

```python
SOLD_SEARCH_FN = lambda c: repo.search_sold_candidates(c.query.split(), c.category, c.size)
```

## Where to find results

- **Deals**: `sqlite3 listings.db "SELECT title, price, market_value, discount_pct, deal_score, listing_url FROM detected_deals ORDER BY deal_score DESC;"` — also printed to stdout when `run_monitor.py` runs. Overwritten (`INSERT OR REPLACE` on `listing_id`) each run, so this always reflects the latest pass, not an accumulating history.
- **Why a listing didn't match** (or did): `sqlite3 listings.db "SELECT fail_reasons, COUNT(*) FROM listing_evaluations WHERE run_at=(SELECT MAX(run_at) FROM listing_evaluations) GROUP BY fail_reasons;"` — one row per active listing per run, with candidate/comparable counts, estimated value, and which hard filter(s) it failed (`discount`, `age`, `seller_rating`, `buynow`, `makeoffer`, `transactions`, `no_candidates`, `no_comparables_above_threshold`).
- **Which sold listings matched a given active listing**: `sqlite3 listings.db "SELECT cm.sold_listing_id, sl.title, sl.sold_price, cm.similarity_score FROM comparable_matches cm JOIN sold_listings sl ON sl.listing_id=cm.sold_listing_id WHERE cm.active_listing_id='<id>';"`

## Project structure

```
price-tracker/
├── src/
│   ├── models.py                     # Dataclasses: Listing, ComparableSearchCriteria,
│   │                                 #   MarketComparable, MarketValuation, DealCriteria, DealScore
│   ├── analysis/
│   │   ├── comparable_search.py      # Per-listing sold-comp search + caching
│   │   ├── matching.py               # Title similarity scoring
│   │   ├── pricing.py                # Market value estimation (weighted avg)
│   │   └── evaluation.py             # Deal scoring + hard filters
│   ├── monitor/
│   │   ├── poller.py                 # Grailed API access: bulk active fetch, per-listing
│   │   │                             #   sold search, deep sold seed collector
│   │   ├── detector.py               # (stub) new-listing detection
│   │   ├── alerter.py                # (stub) Discord/Telegram alerts
│   │   └── scheduler.py              # (stub) recurring polling loop
│   ├── storage/
│   │   ├── repository.py             # SQLite data access layer (see schema below)
│   │   └── exporters.py              # (stub) export deals to JSON
│   └── utils/
│       ├── text.py                   # clean_title() for building search queries
│       ├── time.py                   # listing-age helpers
│       ├── stats.py                  # (empty)
│       └── images.py                 # (empty)
│
├── data/
│   ├── active/grailed_listings.json  # Active Chrome Hearts listings (refreshed by poller.py)
│   ├── sold/grailed_sold.json        # Sold Chrome Hearts listings (dev/test seed data)
│   └── config/                       # brand_aliases.yml, category_map.yml — currently empty, unused
│
├── scripts/
│   ├── backfill_sold.py              # Load JSON into listings.db
│   ├── run_monitor.py                # Entry point — one-shot evaluation pass
│   └── test_db.py                    # Manual DB sanity check
│
└── listings.db                        # SQLite database (see schema below)
```

## Database schema (`listings.db`)

| Table | Purpose |
|---|---|
| `active_listings` / `sold_listings` | Raw listing data, upserted by `listing_id` |
| `sold_comparable_cache` | Which sold listings were fetched for an active listing, and when (TTL-based reuse) |
| `listing_evaluations` | Per-run outcome for every active listing: candidate/comparable counts, valuation, score, pass/fail + `fail_reasons` |
| `comparable_matches` | The sold listings that actually scored as comparables for an active listing, per run |
| `detected_deals` | Listings that passed every hard filter, with market value/discount/score |
| `price_history` | Schema exists for tracking price changes over time — not yet populated (see TODO.md) |

## Configuration

Deal criteria (`src/models.py:DealCriteria`):
```python
DealCriteria(
    min_discount_pct=0.30,      # 30% under market
    min_seller_rating=3.0,
    min_transactions=1,
    max_listing_age_days=180,
    require_buynow=True,
    require_makeoffer=True,
    title_similarity_threshold=0.6,
)
```

Scraping depth (`src/monitor/poller.py`): `DEFAULT_HITS_PER_PAGE = 100`, `DEFAULT_MAX_PAGES = 25` (up to 2,500 items per bulk fetch). Comparable-search cache TTL (`src/analysis/comparable_search.py`): `DEFAULT_CACHE_TTL_SECONDS = 300` (5 minutes).

## Current status

**Implemented**: API polling with pagination and designer/category filters, per-listing live sold-comparable search with caching, title-similarity scoring, market value estimation, deal scoring with hard filters, full per-run tracking (`listing_evaluations`, `comparable_matches`, `detected_deals`).

**Not yet implemented**: `src/monitor/scheduler.py`, `detector.py`, and `alerter.py` are still stubs — there's no recurring polling loop yet, just the one-shot `run_monitor.py` pass, and no push notifications (Discord/Telegram) beyond stdout + the database. See [TODO.md](TODO.md) for the current punch list.

---

For the original design doc, see [Architecture.md](Architecture.md). For how the codebase evolved to its current state, see [RESTRUCTURE_SUMMARY.md](RESTRUCTURE_SUMMARY.md).
