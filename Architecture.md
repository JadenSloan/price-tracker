Overview

 Build a real-time monitoring system that:
 1. Polls Grailed API for new listings
 2. Estimates market value from sold data
 3. Scores deals based on discount + seller reliability + urgency signals
 4. Alerts when deals meet criteria (30%+ under market)

 ---
 Architecture

 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 │   Poller    │────▶│  Detector   │────▶│  Evaluator  │
 │ (5min poll) │     │ (new items) │     │ (scoring)   │
 └─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
       ┌────────────────────────────────────────┼────────────────┐
       │                                        │                │
       ▼                                        ▼                ▼
 ┌─────────────┐                        ┌─────────────┐   ┌─────────────┐
 │  SQLite DB  │◀───────────────────────│  Matcher    │   │   Alerter   │
 │ (sold data) │                        │ (title sim) │   │  (console)  │
 └─────────────┘                        └─────────────┘   └─────────────┘

 ---
 Module Structure

 src/
   models.py              # Add: MarketValuation, DealScore dataclasses
   analysis/
     matching.py          # Title similarity + comparable finding
     pricing.py           # Market value estimation (weighted avg)
     evaluation.py        # Deal scoring logic
   monitor/               # NEW
     __init__.py
     poller.py            # API polling with pagination
     detector.py          # New listing detection
     alerter.py           # Console alerts (extensible to Discord/etc)
     scheduler.py         # Main orchestrator loop
   storage/
     repository.py        # NEW: SQLite data access layer
     loaders.py           # Load JSON into DB
     exporters.py         # Export deals to JSON
 scripts/
   run_monitor.py         # Entry point
   backfill_sold.py       # Populate DB from existing JSON

 ---
 Key Components

 1. Market Value Estimation (pricing.py)

 Algorithm: Weighted Comparable Sales
 - Find sold listings matching: category + size + title similarity (>60%)
 - Weight each comparable by:
   - Recency: exponential decay (half-life 30 days)
   - Similarity: title match score (0.0-1.0)
   - Condition: adjustment factor for condition differences
 - Calculate weighted average of sold prices
 - Output confidence score based on # comparables and their quality

 2. Title Matching (matching.py)

 Hybrid scoring:
 - Token Jaccard similarity (60% weight)
 - Sequence matching ratio (40% weight)
 - Minimum threshold: 0.6

 Filters before matching:
 - Same category (tops, accessories, etc.)
 - Compatible size

 3. Deal Scoring (evaluation.py)

 Formula:
 composite_score = (
     0.50 * discount_score +     # (market - ask) / market, capped at 50%
     0.25 * seller_score +       # rating + transaction history
     0.15 * urgency_score +      # price drop count
     0.10 * demand_score         # heat/likes
 ) * confidence

 Hard filters (must pass all):
 - Discount >= 30%
 - Buynow + Makeoffer enabled
 - Seller rating >= 3.0
 - Seller transactions >= 1
 - Listing age <= 180 days

 4. Storage (repository.py)

 SQLite tables:
 - sold_listings - historical sales for comparables
 - active_listings - tracked active items
 - detected_deals - deals found (for review/analysis)
 - price_history - track price changes over time

 5. Real-Time Monitor (scheduler.py)

 Loop every 5 minutes:
 1. Poll API (3 pages x 40 items = 120 listings)
 2. Filter to new listings (not seen before)
 3. For each new listing:
   - Find comparables from sold DB
   - Estimate market value
   - Calculate deal score
   - If passes criteria → alert + save
 4. Sleep until next cycle

 6. Alerter (alerter.py)

 Discord/Telegram webhook integration:
 - Send formatted deal alerts with:
   - Item title, price, market value, discount %
   - Seller info (name, rating, transactions)
   - Direct link to listing
   - Comparable sales summary
 - Fallback to console if webhook fails
 - Rate limit protection (max 1 msg/second)

 ---
 Implementation Phases

 Phase 1: Data Layer

 - Create storage/repository.py with SQLite schema
 - Implement storage/loaders.py to backfill from JSON
 - Create scripts/backfill_sold.py

 Phase 2: Analysis Core

 - Implement TitleMatcher in matching.py
 - Implement estimate_market_value() in pricing.py
 - Add MarketValuation, MarketComparable to models.py

 Phase 3: Deal Evaluation

 - Implement DealEvaluator in evaluation.py
 - Add DealScore, DealCriteria to models.py
 - Unit tests for scoring logic

 Phase 4: Monitor

 - Create monitor/poller.py with pagination
 - Create monitor/detector.py for new item tracking
 - Create monitor/alerter.py (console output)
 - Create monitor/scheduler.py orchestrator

 Phase 5: Entry Points

 - Create scripts/run_monitor.py
 - Add configuration file support
 - Export deals to JSON for review

 ---
 Critical Files to Modify

 | File                       | Changes                                                  |
 |----------------------------|----------------------------------------------------------|
 | src/models.py              | Add MarketValuation, DealScore, DealCriteria dataclasses |
 | src/analysis/matching.py   | Implement TitleMatcher class                             |
 | src/analysis/pricing.py    | Implement estimate_market_value()                        |
 | src/analysis/evaluation.py | Implement DealEvaluator class                            |
 | src/storage/repository.py  | NEW: SQLite repository                                   |
 | src/monitor/scheduler.py   | NEW: Main orchestrator                                   |

 ---
 Configuration Defaults

 DealCriteria(
     min_discount_pct=0.30,      # 30% under market
     min_seller_rating=3.0,
     min_transactions=1,
     max_listing_age_days=180,
     require_buynow=True,
     require_makeoffer=True
 )

 poll_interval_minutes=5
 hits_per_page=40
 max_pages=3
 title_similarity_threshold=0.6