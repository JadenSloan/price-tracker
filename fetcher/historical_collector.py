import asyncio 
import re 
import json
from playwright.async_api import async_playwright 
from pathlib import Path
from fetcher.grailed_listener import extract_from_algolia_requests  



# Collect sold listings for Grailed 



OUTFILE = Path("data/sold_grailed_listings.json")

# Match Algolia's multi-queries endpoint (hostnames can rotate)
ALGOLIA_URL_RX = re.compile(r"\.algolia\.net/1/indexes/.+/queries", re.I)

async def main(): 

    seen = set()
    rows = []
    raw_rows = []  

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
            await extract_from_algolia_requests(data, seen, rows, raw_rows)  

        # "Listen" to every network response and filter by the regex above           
        page.on("response", handle_response) 

        # Navigate to grailed to trigger network responses
        await page.goto("https://www.grailed.com/sold?designers=Chrome%2520Hearts")

        # Scroll to trigger additional Algolia loads (infinite scroll)
        for _ in range(2):
            await page.mouse.wheel(0,600)
            await page.wait_for_timeout(1000)

        # Save results 
        OUTFILE.write_text(json.dumps(rows, indent=2))
        print(f"Saved {len(rows)} listings to {OUTFILE.resolve()}")

        await browser.close() 

if __name__ == "__main__":
    asyncio.run(main())