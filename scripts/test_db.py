"""Test database to verify rows were inserted properly."""
import sqlite3
from pathlib import Path

def test_database():
    """Check database tables and row counts."""
    db_path = Path(__file__).parent.parent / "listings.db"

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return

    print(f"✅ Database found: {db_path}")
    print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB")
    print("\n" + "=" * 70)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row  # Return rows as dictionaries
    cur = con.cursor()

    # Check each table
    tables = ["sold_listings", "active_listings", "detected_deals", "price_history"]

    for table in tables:
        print(f"\n📊 {table.upper()}")
        print("-" * 70)

        # Count rows
        cur.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cur.fetchone()["count"]
        print(f"   Total rows: {count}")

        if count > 0:
            # Show sample row
            cur.execute(f"SELECT * FROM {table} LIMIT 1")
            row = cur.fetchone()
            print(f"   Sample row:")
            print(f"     - ID: {row['listing_id']}")
            print(f"     - Title: {row['title']}")
            print(f"     - Price: ${row['price']}")
            if row['sold_price']:
                print(f"     - Sold Price: ${row['sold_price']}")
            print(f"     - Designer: {row['designer']}")
            print(f"     - Seller: {row['seller_name']} (rating: {row['seller_rating']})")

            # Show column info
            cur.execute(f"PRAGMA table_info({table})")
            columns = cur.fetchall()
            print(f"   Columns: {len(columns)}")

    print("\n" + "=" * 70)
    print("✅ Database test complete!")

    con.close()


def query_sold_items(limit=10):
    """Query and display sold items."""
    db_path = Path(__file__).parent.parent / "listings.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    print(f"\n🔍 TOP {limit} SOLD LISTINGS")
    print("=" * 70)

    cur.execute(f"""
        SELECT listing_id, title, sold_price, designer, seller_rating
        FROM sold_listings
        ORDER BY sold_price DESC
        LIMIT {limit}
    """)

    rows = cur.fetchall()

    for i, row in enumerate(rows, 1):
        print(f"\n{i}. {row['title']}")
        print(f"   Sold for: ${row['sold_price']}")
        print(f"   Designer: {row['designer']}")
        print(f"   Seller rating: {row['seller_rating']}")
        print(f"   ID: {row['listing_id']}")

    con.close()


def verify_data_integrity():
    """Check for data quality issues."""
    db_path = Path(__file__).parent.parent / "listings.db"
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    print("\n🔍 DATA INTEGRITY CHECK")
    print("=" * 70)

    # Check for NULL values in important fields
    checks = [
        ("sold_listings with NULL title", "SELECT COUNT(*) FROM sold_listings WHERE title IS NULL"),
        ("sold_listings with NULL sold_price", "SELECT COUNT(*) FROM sold_listings WHERE sold_price IS NULL OR sold_price = 0"),
        ("sold_listings with NULL designer", "SELECT COUNT(*) FROM sold_listings WHERE designer IS NULL"),
        ("active_listings with NULL price", "SELECT COUNT(*) FROM active_listings WHERE price IS NULL OR price = 0"),
    ]

    issues_found = False

    for check_name, query in checks:
        cur.execute(query)
        count = cur.fetchone()[0]
        if count > 0:
            print(f"⚠️  {check_name}: {count} rows")
            issues_found = True
        else:
            print(f"✅ {check_name}: None")

    if not issues_found:
        print("\n✅ No data integrity issues found!")

    con.close()


if __name__ == "__main__":
    # Run all tests
    test_database()
    query_sold_items(limit=5)
    verify_data_integrity()
