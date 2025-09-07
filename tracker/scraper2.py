import asyncio
import json
import re 
from pathlib import Path
from playwright.async_api import async_playwright

# Match Algolia's multi-queries endpoint (hostnames can rotate)
ALGOLIA_URL_RX = re.compile(r"\.algolia\.net/1/indexes/\*/queries", re.I)

LISTINGS_INDEX_SUBSTR = "listing"

OUTFILE = Path("grailed_listings.json")


def extract_from_algolia_payload(payload: dict, seen: set, rows: list) -> None:
    for r in payload.get("results", []):
        idx = (r.get("index") or r.get("indexName") or "").lower()
        if LISTINGS_INDEX_SUBSTR not in idx:
            continue # skip suggestions/brands/etc.


        for hit in r.get("hits", []):
            # Choose a stable identifier
            cover = hit.get("cover_photo", {}) or {}
            listing_id = (
            cover.get("listing_id")
            or cover.get("id")
)
            if not listing_id or listing_id in seen: 
                continue
            seen.add(listing_id)

            user = hit.get("user", {}) or {}
            seller_score = user.get("seller_score", {}) or {} 

            row = {
                "listing_id": listing_id,
                "title": hit.get("title"),
                "price": hit.get("price"),
                "size": hit.get("size"), 
                "created_at": hit.get("created_at"),
                "updated_at": hit.get("price_updated_at") or hit.get("updated_at"),
                # Build a URL if the payload doesn't include one
                "url": hit.get("url") or f"https://www.grailed.com/listings/{listing_id}",
                # Seller fields from user
                "seller_id": user.get("id"),
                "seller_username": user.get("username"),
                "rating_average": seller_score.get("rating_average"),
                "rating_count": seller_score.get("rating_count"),
            }

            rows.append(row) 

async def main(): 
    seen = set() 
    rows = []

    async with async_playwright() as pw: 
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page() 

        async def handle_response(resp): 
            url = resp.url
            if not ALGOLIA_URL_RX.search(url):
                return
            try:
                data = await resp.json()
            except Exception: 
                return 
            extract_from_algolia_payload(data, seen, rows)

        # "Listen" to every network response and filter by the regex above
        page.on("response", handle_response) 

        # Open a search page (change the query to whatever you like)
        await page.goto("https://www.grailed.com/shop?query=chrome%20hearts", wait_until="domcontentloaded")

        # Scroll to trigger additional Algolia loads (infinite scroll)
        for _ in range(2):
            await page.mouse.wheel(0, 6000)
            await page.wait_for_timeout(1200)

        # Save results
        OUTFILE.write_text(json.dumps(rows, indent=2))
        print(f"Saved {len(rows)} listings to {OUTFILE.resolve()}")

        await browser.close() 

if __name__ == "__main__":
    asyncio.run(main())







