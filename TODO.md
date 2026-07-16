# TODO

_Last updated: July 16, 2026_

## Real-time monitoring
- [ ] Implement `src/monitor/scheduler.py` — wrap `run_monitor.py`'s one-shot pass in a real recurring loop (cron, APScheduler, or a long-running process).
- [ ] Implement `src/monitor/detector.py` — track which active listings have already been evaluated/alerted on, so a recurring loop only acts on genuinely new listings instead of re-scoring everything every cycle.
- [ ] Implement `src/monitor/alerter.py` — push notifications (Discord/Telegram webhook) when a deal is found. Right now deals only land in stdout + the `detected_deals` table.

## Data coverage
- [ ] Map Grailed's per-category size enums (`Tops.sizes.M`, `Accessories.sizes.OS`, etc.) to our stored size strings so `search_sold_listings()` can filter by size server-side instead of the current local post-filter — see `src/monitor/poller.py::CATEGORY_ENUM_MAP` for the category-side version that's already done.
- [ ] Consider splitting the bulk scrape by category/department (not just designer) if a single paginated `designers=["Chrome Hearts"]` pull stops surfacing even coverage across categories as inventory grows.

## Price tracking
- [ ] `price_history` table exists in the schema but nothing writes to it yet — decide when/how to snapshot price changes (e.g. on each poller run, diff against the last known price and insert a row).
- [ ] `repository.update_listing_price()` exists but has no caller — wire it into whatever re-fetches an active listing's current price.

## Housekeeping
- [x] ~~Fix messy titles~~ — done via `src/utils/text.py::clean_title()`.
- [x] ~~Filter function for hard criteria (buynow/makeoffer/rating/transactions/age)~~ — done via `src/analysis/evaluation.py::hard_filter_failures()`.
- [ ] `requirement.txt` still lists `playwright`/`asyncio`/`re` from an earlier approach — the only real dependency is `grailed_api`. Worth fixing or replacing with a proper `pyproject.toml` (currently empty).
- [ ] `data/config/brand_aliases.yml` and `category_map.yml` are empty and unused — either wire them in (e.g. multi-brand support, category label normalization) or remove them.
- [ ] No automated test suite yet (`pytest` is installed in `.venv`, no `tests/` directory exists) — `scripts/test_db.py` is a manual sanity-check script, not a real suite.
