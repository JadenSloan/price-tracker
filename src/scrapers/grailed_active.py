import re 
import json 
from pathlib import Path
from src.models import Listing
from dataclasses import dataclass, asdict 
from src.utils.time import days_old
from grailed_api import GrailedAPICLient 

OUTFILE = Path("data/active/grailed_listings.json")
RAW_OUTFILE = Path("data/active/raw_grailed_listings.json")

client = GrailedAPICLient()

def get_active_listings(payload: dict, rows: list, raw_rows: list):

    products = client.find_products(
        sold=False, 
        query_search="chrome hearts"
    )

    listings = [] 

    for product in products: 
        listing = Listing(
            listing_id=product.get("listing_id"), 
            title=product.get("title"), 
            price=product.get("price"), 
            size=product.get("size"), 
            listing_url=product.get("url"),
            posted_time=product.get("created_at"),
            bumped_time=product.get("updated_at"),  
            seller_name=product.get("user").get("username"),  
            seller_rating=product.get("user").get("rating_average"), 
            rating_count=product.get("user").get("rating_count"),  
            location=product.get("location"),  
            designer=product.get("designer_names"),  
            condition=product.get("condition"),  
            image_url=product.get("url"),  
            sold_price=product.get("sold_price"), 
            transactions=product.get("user").get("total_bought_and_sold"),  
            category=product.get("category"),  
            buynow=product.get("buynow"), 
            makeoffer=product.get("makeoffer"),
            sold=product.get("sold")
        )

            # Collect data before filters.
        raw_rows.append(asdict(listings))

        # Prefilters 
        age_days = days_old(listing.posted_time)

        if not (listing.buynow and listing.makeoffer):
            continue
        if listing.seller_rating is None or listing.seller_rating < 3:
            continue 
        if listing.transactions == 0:
            continue
        if age_days > 180:
            continue 
        if listing.sold:
            continue

        rows.append(asdict(listings))
          
    


async def main(): 

    seen = set()
    rows = []
    raw_rows = []

    
    # Save results 
    OUTFILE.write_text(json.dumps(rows, indent=2))
    print(f"Saved {len(rows)} listings to {OUTFILE.resolve()}")

    # Save raw results
    RAW_OUTFILE.write_text(json.dumps(raw_rows, indent=2))
    print(f"Saved {len(raw_rows)} listings to {RAW_OUTFILE.resolve()}")


if __name__ == "__main__":
    main()


          

