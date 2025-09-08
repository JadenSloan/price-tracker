from playwright.async_api import async_playwright 
import asyncio 
import re 
import json 
from pathlib import Path
from src.models import Listing
from dataclasses import dataclass, asdict 
from utils.time import days_old

OUTFILE = Path("grailed_listings.json")



async def extract_from_algolia_requests(payload: dict, seen: set, rows: list):
    # Algolia's response contains a list of hits under results[*]['hits']
    for results in payload.get("results", []):
        for hit in results.get("hits", []):

            cover = hit.get("cover_photo", {}) or {}
            listing_id = cover.get("listing_id")

            if not listing_id or listing_id in seen:
                continue
            seen.add(listing_id)

            user = hit.get("user", {}) or {}
            score = user.get("seller_score") or {} 
            
            
            listing = Listing(
                listing_id=listing_id, 
                title=hit.get("title"),
                price=hit.get("price"),
                size=hit.get("size"),
                condition=hit.get("condition"),
                bumped_time=hit.get("bumped_at"),
                location=hit.get("location"),
                designer=hit.get("designer_names"),
                sold_price=hit.get("sold_price"),
                category=hit.get("category"),
                buynow=hit.get("buynow"),
                makeoffer=hit.get("makeoffer"),
                sold=hit.get("sold"),
                seller_name=user.get("username"),
                transactions=user.get("total_bought_and_sold"),
                seller_rating=score.get("rating_average"),
                rating_count=score.get("rating_count"),
                image_url=cover.get("image_url"),
                posted_time=cover.get("created_at"),
                listing_url=f"https://www.grailed.com/listings/{listing_id}"
            )

            # Prefilters 
            age_days = days_old(listing.posted_time)

            if not listing.buynow and not listing.makeoffer:
                continue

            if listing.seller_rating is None or listing.seller_rating < 3:
                continue 

            if listing.transactions == 0:
                continue

            if age_days > 180:
                continue 

            if listing.sold:
                continue

            rows.append(asdict(listing))
          
    



# Match Algolia's multi-queries endpoint (hostnames can rotate)
ALGOLIA_URL_RX = re.compile(r"\.algolia\.net/1/indexes/.+/queries", re.I)

async def main(): 

    seen = set()
    rows = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        async def handle_response(resp): 
            url = resp.request.url
            if not ALGOLIA_URL_RX.search(url): 
                return 
            try: 
                data = await resp.json()
            except Exception:
                return 
            await extract_from_algolia_requests(data, seen, rows)

        # "Listen" to every network response and filter by the regex above           
        page.on("response", handle_response) 

        # Navigate to grailed to trigger network responses
        await page.goto("https://www.grailed.com/designers/chrome-hearts")

        # Scroll to trigger additional Algolia loads (infinite scroll)
        for _ in range(2):
            await page.mouse.wheel(0,600)
            await page.wait_for_timeout(1000)

        # Save results
        OUTFILE.write_text(json.dumps(rows, indent=2))
        print(f"Saved {len(rows)} listings to {OUTFILE.resolve()}")

        # Let all responses finish
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(1500)
        
        await browser.close() 

if __name__ == "__main__":
    asyncio.run(main())


            

