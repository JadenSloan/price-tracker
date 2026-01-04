# Price Tracker - Grailed Deal Finder

A tool for finding deals on Grailed by comparing active listings against historical sold prices.

## Project Structure

```
price-tracker/
├── src/                          # Source code
│   ├── scrapers/                 # Data collection
│   │   ├── grailed_active.py    # Scrape active listings
│   │   └── grailed_sold.py      # Scrape sold listings
│   ├── analysis/                 # Deal finding logic
│   │   ├── matching.py          # Text similarity & filtering
│   │   ├── pricing.py           # Market value calculation
│   │   └── evaluation.py        # Deal detection
│   ├── processing/               # Data transformation
│   │   └── cleaners.py          # Title cleaning & normalization
│   ├── storage/                  # I/O operations
│   │   ├── loaders.py           # Load JSON files
│   │   └── exporters.py         # Export results
│   ├── utils/                    # Shared utilities
│   │   ├── stats.py             # Statistical functions
│   │   ├── text.py              # Text processing
│   │   └── time.py              # Time utilities
│   ├── models.py                # Data models
│   ├── config.py                # Configuration
│   └── main.py                  # Main entry point
│
├── data/                         # Data files
│   ├── active/                  # Active listings
│   │   ├── grailed_listings.json
│   │   ├── grailed_listings_clean.json
│   │   └── raw_grailed_listings.json
│   ├── sold/                    # Historical sales
│   │   └── grailed_sold.json
│   ├── deals/                   # Found deals
│   │   └── deals.json
│   └── config/                  # Configuration
│       ├── brand_aliases.yml
│       └── category_map.yml
│
├── scripts/                     # Entry point scripts
│   ├── collect_active.py       # Run active listings scraper
│   ├── collect_sold.py         # Run sold listings scraper
│   └── find_deals.py           # Run deal finder
│
└── tests/                       # Tests
```

## Usage

### 1. Collect Active Listings
```bash
python scripts/collect_active.py
```
Scrapes current Chrome Hearts listings from Grailed and saves to `data/active/grailed_listings.json`

### 2. Collect Sold Listings
```bash
python scripts/collect_sold.py
```
Scrapes sold Chrome Hearts listings for market value comparison and saves to `data/sold/grailed_sold.json`

### 3. Clean Titles (Optional)
```bash
python -m src.processing.cleaners
```
Normalizes listing titles for better matching

### 4. Find Deals
```bash
python scripts/find_deals.py
# OR
python -m src.main
```
Analyzes active listings against sold comparables and outputs deals to `data/deals/deals.json`

## How It Works

1. **Scraping**: Collects active and sold listings using Playwright to intercept Grailed's Algolia API
2. **Matching**: Finds comparable sold items using text similarity (Jaccard) and filters (category, size, condition)
3. **Pricing**: Calculates market value from comparable sales using weighted median
4. **Evaluation**: Identifies deals (15-20%+ below market value) with confidence scores
5. **Output**: Saves results to JSON and displays summary in terminal

## Requirements

- Python 3.10+
- Playwright
- See `requirements.txt` for full dependencies

## Configuration

- Brand aliases: `data/config/brand_aliases.yml`
- Category mappings: `data/config/category_map.yml`
- Deal thresholds: Configurable in `src/analysis/evaluation.py`

## Next Steps

To complete the deal finder implementation, see the plan at `.claude/plans/jiggly-dreaming-adleman.md`
