"""
Complete SQLite data access layer implementation.

This is a reference implementation showing best practices for a repository pattern.
It provides a clean API to interact with the database without writing SQL everywhere.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


# Database path
DB_PATH = Path(__file__).parent.parent.parent / "listings.db"


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_connection():
    """
    Context manager for database connections.

    Ensures connections are properly closed and transactions are committed.

    Usage:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sold_listings")
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    try:
        yield conn
        conn.commit()  # Auto-commit on success
    except Exception:
        conn.rollback()  # Rollback on error
        raise
    finally:
        conn.close()


def get_cursor():
    """Get a cursor with a connection (less safe than context manager)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()


# ============================================================================
# SCHEMA CREATION
# ============================================================================

def create_tables():
    """Create all database tables if they don't exist."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Sold listings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sold_listings (
                listing_id TEXT PRIMARY KEY,
                title TEXT,
                price INTEGER,
                size TEXT,
                listing_url TEXT,
                posted_time TEXT,
                bumped_time TEXT,
                seller_name TEXT,
                seller_rating REAL,
                rating_count INTEGER,
                location TEXT,
                designer TEXT,
                condition TEXT,
                image_url TEXT,
                sold_price INTEGER,
                transactions INTEGER,
                category TEXT,
                buynow INTEGER,
                makeoffer INTEGER,
                sold INTEGER,
                date_sold TEXT
            )
        """)

        # Active listings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS active_listings (
                listing_id TEXT PRIMARY KEY,
                title TEXT,
                price INTEGER,
                size TEXT,
                listing_url TEXT,
                posted_time TEXT,
                bumped_time TEXT,
                seller_name TEXT,
                seller_rating REAL,
                rating_count INTEGER,
                location TEXT,
                designer TEXT,
                condition TEXT,
                image_url TEXT,
                sold_price INTEGER,
                transactions INTEGER,
                category TEXT,
                buynow INTEGER,
                makeoffer INTEGER,
                sold INTEGER,
                date_sold TEXT
            )
        """)

        # Detected deals table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detected_deals (
                listing_id TEXT PRIMARY KEY,
                title TEXT,
                price INTEGER,
                size TEXT,
                listing_url TEXT,
                posted_time TEXT,
                bumped_time TEXT,
                seller_name TEXT,
                seller_rating REAL,
                rating_count INTEGER,
                location TEXT,
                designer TEXT,
                condition TEXT,
                image_url TEXT,
                sold_price INTEGER,
                transactions INTEGER,
                category TEXT,
                buynow INTEGER,
                makeoffer INTEGER,
                sold INTEGER,
                date_sold TEXT,
                market_value REAL,
                discount_pct REAL,
                deal_score REAL,
                detected_at TEXT
            )
        """)

        # Price history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT,
                price INTEGER,
                recorded_at TEXT,
                FOREIGN KEY (listing_id) REFERENCES active_listings(listing_id)
            )
        """)

        # Cache of sold-listing comparables found for a given active listing,
        # so a poll loop doesn't re-search live every cycle.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sold_comparable_cache (
                active_listing_id TEXT NOT NULL,
                sold_listing_id TEXT NOT NULL,
                query TEXT,
                cached_at TEXT NOT NULL,
                PRIMARY KEY (active_listing_id, sold_listing_id),
                FOREIGN KEY (active_listing_id) REFERENCES active_listings(listing_id)
            )
        """)

        # Per-run outcome for every active listing evaluated by run_monitor.py
        # (whether or not it passed), so "why did this listing not match" is
        # queryable after the fact instead of only visible in stdout.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS listing_evaluations (
                active_listing_id TEXT NOT NULL,
                run_at TEXT NOT NULL,
                candidate_count INTEGER,
                comparable_count INTEGER,
                estimated_value REAL,
                confidence REAL,
                discount_pct REAL,
                composite_score REAL,
                passes_hard_filters INTEGER,
                fail_reasons TEXT,
                PRIMARY KEY (active_listing_id, run_at),
                FOREIGN KEY (active_listing_id) REFERENCES active_listings(listing_id)
            )
        """)

        # The sold listings that actually scored as comparables (passed the
        # title-similarity threshold in matching.find_comparables) for a given
        # active listing, per run.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comparable_matches (
                active_listing_id TEXT NOT NULL,
                sold_listing_id TEXT NOT NULL,
                run_at TEXT NOT NULL,
                similarity_score REAL,
                weight REAL,
                PRIMARY KEY (active_listing_id, sold_listing_id, run_at),
                FOREIGN KEY (active_listing_id) REFERENCES active_listings(listing_id)
            )
        """)


# ============================================================================
# CREATE OPERATIONS (Insert)
# ============================================================================

def save_sold_listing(listing: Dict[str, Any]) -> None:
    """
    Insert or replace a sold listing.

    Args:
        listing: Dictionary with listing data (from JSON)

    Example:
        listing = {
            "listing_id": "12345",
            "title": "Chrome Hearts Ring",
            "sold_price": 500,
            ...
        }
        save_sold_listing(listing)
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO sold_listings (
                listing_id, title, price, size, listing_url, posted_time,
                bumped_time, seller_name, seller_rating, rating_count,
                location, designer, condition, image_url, sold_price,
                transactions, category, buynow, makeoffer, sold, date_sold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing.get("listing_id"),
            listing.get("title"),
            listing.get("price"),
            listing.get("size"),
            listing.get("listing_url"),
            listing.get("posted_time"),
            listing.get("bumped_time"),
            listing.get("seller_name"),
            listing.get("seller_rating"),
            listing.get("rating_count"),
            listing.get("location"),
            listing.get("designer"),
            listing.get("condition"),
            listing.get("image_url"),
            listing.get("sold_price"),
            listing.get("transactions"),
            listing.get("category"),
            listing.get("buynow"),
            listing.get("makeoffer"),
            listing.get("sold"),
            listing.get("date_sold")
        ))


def save_active_listing(listing: Dict[str, Any]) -> None:
    """Insert or replace an active listing."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO active_listings (
                listing_id, title, price, size, listing_url, posted_time,
                bumped_time, seller_name, seller_rating, rating_count,
                location, designer, condition, image_url, sold_price,
                transactions, category, buynow, makeoffer, sold, date_sold
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing.get("listing_id"),
            listing.get("title"),
            listing.get("price"),
            listing.get("size"),
            listing.get("listing_url"),
            listing.get("posted_time"),
            listing.get("bumped_time"),
            listing.get("seller_name"),
            listing.get("seller_rating"),
            listing.get("rating_count"),
            listing.get("location"),
            listing.get("designer"),
            listing.get("condition"),
            listing.get("image_url"),
            listing.get("sold_price"),
            listing.get("transactions"),
            listing.get("category"),
            listing.get("buynow"),
            listing.get("makeoffer"),
            listing.get("sold"),
            listing.get("date_sold")
        ))


def save_deal(deal: Dict[str, Any]) -> None:
    """Save a detected deal to the database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO detected_deals (
                listing_id, title, price, size, listing_url, posted_time,
                bumped_time, seller_name, seller_rating, rating_count,
                location, designer, condition, image_url, sold_price,
                transactions, category, buynow, makeoffer, sold, date_sold,
                market_value, discount_pct, deal_score, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deal.get("listing_id"),
            deal.get("title"),
            deal.get("price"),
            deal.get("size"),
            deal.get("listing_url"),
            deal.get("posted_time"),
            deal.get("bumped_time"),
            deal.get("seller_name"),
            deal.get("seller_rating"),
            deal.get("rating_count"),
            deal.get("location"),
            deal.get("designer"),
            deal.get("condition"),
            deal.get("image_url"),
            deal.get("sold_price"),
            deal.get("transactions"),
            deal.get("category"),
            deal.get("buynow"),
            deal.get("makeoffer"),
            deal.get("sold"),
            deal.get("date_sold"),
            deal.get("market_value"),
            deal.get("discount_pct"),
            deal.get("deal_score"),
            deal.get("detected_at")
        ))


def bulk_insert_sold_listings(listings: List[Dict[str, Any]]) -> int:
    """
    Insert multiple sold listings efficiently.

    Args:
        listings: List of listing dictionaries

    Returns:
        Number of listings inserted

    Example:
        listings = json.load(open("data/sold/grailed_sold.json"))
        count = bulk_insert_sold_listings(listings)
        print(f"Inserted {count} listings")
    """
    with get_connection() as conn:
        cur = conn.cursor()

        for listing in listings:
            cur.execute("""
                INSERT OR REPLACE INTO sold_listings (
                    listing_id, title, price, size, listing_url, posted_time,
                    bumped_time, seller_name, seller_rating, rating_count,
                    location, designer, condition, image_url, sold_price,
                    transactions, category, buynow, makeoffer, sold, date_sold
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                listing.get("listing_id"),
                listing.get("title"),
                listing.get("price"),
                listing.get("size"),
                listing.get("listing_url"),
                listing.get("posted_time"),
                listing.get("bumped_time"),
                listing.get("seller_name"),
                listing.get("seller_rating"),
                listing.get("rating_count"),
                listing.get("location"),
                listing.get("designer"),
                listing.get("condition"),
                listing.get("image_url"),
                listing.get("sold_price"),
                listing.get("transactions"),
                listing.get("category"),
                listing.get("buynow"),
                listing.get("makeoffer"),
                listing.get("sold"),
                listing.get("date_sold")
            ))

        return len(listings)


# ============================================================================
# READ OPERATIONS (Query)
# ============================================================================

def get_all_sold_listings() -> List[Dict[str, Any]]:
    """Get all sold listings from the database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sold_listings")
        return [dict(row) for row in cur.fetchall()]


def get_sold_listing_by_id(listing_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific sold listing by ID.

    Args:
        listing_id: The listing ID to search for

    Returns:
        Listing dictionary or None if not found
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sold_listings WHERE listing_id = ?", (listing_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_active_listings() -> List[Dict[str, Any]]:
    """Get all active listings."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM active_listings")
        return [dict(row) for row in cur.fetchall()]


def get_active_listing_by_id(listing_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific active listing by ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM active_listings WHERE listing_id = ?", (listing_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def find_sold_by_category_and_size(category: str, size: str) -> List[Dict[str, Any]]:
    """
    Find sold listings matching category and size.

    This is used to find comparables for market value calculation.

    Args:
        category: Listing category (e.g., "tops", "accessories")
        size: Item size (e.g., "m", "l", "one size")

    Returns:
        List of matching sold listings

    Example:
        comparables = find_sold_by_category_and_size("tops", "m")
        print(f"Found {len(comparables)} comparable items")
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM sold_listings
            WHERE category = ? AND size = ?
            AND sold_price > 0
            ORDER BY date_sold DESC
        """, (category, size))
        return [dict(row) for row in cur.fetchall()]


def search_sold_by_title(keyword: str) -> List[Dict[str, Any]]:
    """
    Search sold listings by title keyword.

    Args:
        keyword: Search term (case-insensitive)

    Returns:
        List of matching listings

    Example:
        rings = search_sold_by_title("ring")
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM sold_listings
            WHERE title LIKE ?
            ORDER BY sold_price DESC
        """, (f"%{keyword}%",))
        return [dict(row) for row in cur.fetchall()]


def search_sold_candidates(
    keywords: List[str], category: str = "", size: str = "", min_keyword_matches: int = 1
) -> List[Dict[str, Any]]:
    """
    Search sold listings by category, size, and title keywords in one query —
    dev-time stand-in for a live Grailed sold-listing search using the same
    criteria (title, category, size) as the real search_fn. Category/size are
    exact (case/whitespace-insensitive) matches: an active listing with no
    category or size naturally matches nothing, same as the old post-filter.

    Args:
        keywords: Query tokens (e.g. from clean_title().split())
        category: Active listing's category; must match exactly (case-insensitive)
        size: Active listing's size; must match exactly (case-insensitive)
        min_keyword_matches: Minimum number of keywords that must appear in the title

    Returns:
        List of matching sold listings, highest sold price first
    """
    if not keywords:
        return []
    with get_connection() as conn:
        cur = conn.cursor()
        clauses = " + ".join("(title LIKE ?)" for _ in keywords)
        params = [f"%{kw}%" for kw in keywords]
        cur.execute(
            f"""
            SELECT * FROM sold_listings
            WHERE LOWER(TRIM(category)) = LOWER(TRIM(?))
              AND LOWER(TRIM(size)) = LOWER(TRIM(?))
              AND sold_price > 0
              AND ({clauses}) >= ?
            ORDER BY sold_price DESC
            """,
            (category, size, *params, min_keyword_matches),
        )
        return [dict(row) for row in cur.fetchall()]


def get_sold_by_designer(designer: str) -> List[Dict[str, Any]]:
    """Get all sold listings for a specific designer."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM sold_listings
            WHERE designer = ?
            ORDER BY sold_price DESC
        """, (designer,))
        return [dict(row) for row in cur.fetchall()]


def get_recent_sold_listings(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get most recently sold listings.

    Args:
        limit: Maximum number of listings to return

    Returns:
        List of recent sold listings
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM sold_listings
            ORDER BY date_sold DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]


def get_detected_deals(limit: int = 50) -> List[Dict[str, Any]]:
    """Get detected deals, ordered by deal score."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM detected_deals
            ORDER BY deal_score DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]


# ============================================================================
# SOLD-COMPARABLE CACHE
# ============================================================================

def save_comparable_cache(
    active_listing_id: str, sold_listing_ids: List[str], query: str, cached_at: Optional[str] = None
) -> None:
    """Replace the cached sold-comparable links for an active listing."""
    cached_at = cached_at or datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM sold_comparable_cache WHERE active_listing_id = ?", (active_listing_id,))
        cur.executemany(
            """
            INSERT OR REPLACE INTO sold_comparable_cache
                (active_listing_id, sold_listing_id, query, cached_at)
            VALUES (?, ?, ?, ?)
            """,
            [(active_listing_id, sid, query, cached_at) for sid in sold_listing_ids],
        )


def get_cached_comparable_ids(active_listing_id: str) -> List[str]:
    """Get the sold_listing_ids cached for an active listing."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT sold_listing_id FROM sold_comparable_cache WHERE active_listing_id = ?",
            (active_listing_id,),
        )
        return [row["sold_listing_id"] for row in cur.fetchall()]


def is_comparable_cache_fresh(active_listing_id: str, ttl_seconds: int) -> bool:
    """Check whether the cached comparables for an active listing are within TTL."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT MAX(cached_at) as cached_at FROM sold_comparable_cache WHERE active_listing_id = ?",
            (active_listing_id,),
        )
        row = cur.fetchone()
        if row is None or row["cached_at"] is None:
            return False
        cached_at = datetime.fromisoformat(row["cached_at"])
        age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
        return age_seconds <= ttl_seconds


# ============================================================================
# RUN TRACKING (per-run evaluation outcomes + matched comparables)
# ============================================================================

def save_listing_evaluation(
    active_listing_id: str,
    run_at: str,
    candidate_count: int,
    comparable_count: int,
    estimated_value: Optional[float],
    confidence: Optional[float],
    discount_pct: Optional[float],
    composite_score: Optional[float],
    passes_hard_filters: bool,
    fail_reasons: List[str],
) -> None:
    """Record what happened to an active listing during one run_monitor.py pass."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO listing_evaluations (
                active_listing_id, run_at, candidate_count, comparable_count,
                estimated_value, confidence, discount_pct, composite_score,
                passes_hard_filters, fail_reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                active_listing_id, run_at, candidate_count, comparable_count,
                estimated_value, confidence, discount_pct, composite_score,
                int(passes_hard_filters), ",".join(fail_reasons),
            ),
        )


def save_comparable_matches(active_listing_id: str, run_at: str, comparables: List[Any]) -> None:
    """Record the sold listings that scored as comparables (passed the
    title-similarity threshold) for an active listing on a given run.
    `comparables` is a list of MarketComparable-like objects with
    listing_id/similarity_score/weight attributes.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT OR REPLACE INTO comparable_matches
                (active_listing_id, sold_listing_id, run_at, similarity_score, weight)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (active_listing_id, c.listing_id, run_at, c.similarity_score, c.weight)
                for c in comparables
            ],
        )


def get_listing_evaluations(active_listing_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get the most recent evaluation runs for an active listing, newest first."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM listing_evaluations
            WHERE active_listing_id = ?
            ORDER BY run_at DESC
            LIMIT ?
            """,
            (active_listing_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]


def get_comparable_matches(active_listing_id: str, run_at: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get matched sold listings for an active listing, for a specific run
    (or the most recent run if run_at is omitted)."""
    with get_connection() as conn:
        cur = conn.cursor()
        if run_at is None:
            cur.execute(
                "SELECT MAX(run_at) as run_at FROM comparable_matches WHERE active_listing_id = ?",
                (active_listing_id,),
            )
            row = cur.fetchone()
            run_at = row["run_at"] if row else None
            if run_at is None:
                return []
        cur.execute(
            """
            SELECT cm.*, sl.title, sl.sold_price
            FROM comparable_matches cm
            JOIN sold_listings sl ON sl.listing_id = cm.sold_listing_id
            WHERE cm.active_listing_id = ? AND cm.run_at = ?
            ORDER BY cm.weight DESC
            """,
            (active_listing_id, run_at),
        )
        return [dict(row) for row in cur.fetchall()]


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================

def update_listing_price(listing_id: str, new_price: int) -> bool:
    """
    Update the price of an active listing.

    Args:
        listing_id: ID of listing to update
        new_price: New price value

    Returns:
        True if update succeeded, False if listing not found
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE active_listings
            SET price = ?
            WHERE listing_id = ?
        """, (new_price, listing_id))
        return cur.rowcount > 0


def mark_listing_as_sold(listing_id: str) -> bool:
    """Mark an active listing as sold."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE active_listings
            SET sold = 1
            WHERE listing_id = ?
        """, (listing_id,))
        return cur.rowcount > 0


# ============================================================================
# DELETE OPERATIONS
# ============================================================================

def delete_sold_listing(listing_id: str) -> bool:
    """Delete a sold listing by ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM sold_listings WHERE listing_id = ?", (listing_id,))
        return cur.rowcount > 0


def delete_active_listing(listing_id: str) -> bool:
    """Delete an active listing by ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM active_listings WHERE listing_id = ?", (listing_id,))
        return cur.rowcount > 0


def clear_all_sold_listings() -> int:
    """Delete all sold listings (use with caution!)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM sold_listings")
        return cur.rowcount


# ============================================================================
# UTILITY OPERATIONS
# ============================================================================

def count_sold_listings() -> int:
    """Get total number of sold listings."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sold_listings")
        return cur.fetchone()[0]


def count_active_listings() -> int:
    """Get total number of active listings."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM active_listings")
        return cur.fetchone()[0]


def listing_exists(listing_id: str, table: str = "sold_listings") -> bool:
    """
    Check if a listing exists in a table.

    Args:
        listing_id: ID to check
        table: Table name ("sold_listings" or "active_listings")

    Returns:
        True if listing exists
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM {table} WHERE listing_id = ?", (listing_id,))
        return cur.fetchone() is not None


def get_price_stats(table: str = "sold_listings") -> Dict[str, float]:
    """
    Get price statistics for a table.

    Returns:
        Dictionary with min, max, avg, median prices
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Basic stats
        cur.execute(f"""
            SELECT
                MIN(sold_price) as min,
                MAX(sold_price) as max,
                AVG(sold_price) as avg,
                COUNT(*) as count
            FROM {table}
            WHERE sold_price > 0
        """)
        row = cur.fetchone()

        return {
            "min": row["min"],
            "max": row["max"],
            "avg": round(row["avg"], 2) if row["avg"] else 0,
            "count": row["count"]
        }


# ============================================================================
# DEMO / TEST CODE
# ============================================================================

if __name__ == "__main__":
    """Demo showing how to use the repository."""

    print("=" * 70)
    print("REPOSITORY DEMO")
    print("=" * 70)

    # Create tables
    print("\n1. Creating tables...")
    create_tables()
    print("✅ Tables created")

    # Count listings
    print("\n2. Counting listings...")
    sold_count = count_sold_listings()
    active_count = count_active_listings()
    print(f"   Sold listings: {sold_count}")
    print(f"   Active listings: {active_count}")

    # Get price stats
    if sold_count > 0:
        print("\n3. Price statistics:")
        stats = get_price_stats("sold_listings")
        print(f"   Min: ${stats['min']}")
        print(f"   Max: ${stats['max']}")
        print(f"   Avg: ${stats['avg']}")

    # Find comparables
    print("\n4. Finding comparables for 'tops' size 'm':")
    comparables = find_sold_by_category_and_size("tops", "m")
    print(f"   Found {len(comparables)} comparable items")

    if comparables:
        print(f"   Sample: {comparables[0]['title']} - ${comparables[0]['sold_price']}")

    # Search by keyword
    print("\n5. Searching for 'ring' in sold listings:")
    rings = search_sold_by_title("ring")
    print(f"   Found {len(rings)} items")

    if rings:
        for i, ring in enumerate(rings[:3], 1):
            print(f"   {i}. {ring['title']} - ${ring['sold_price']}")

    print("\n" + "=" * 70)
    print("✅ Demo complete!")
