from unicodedata import category
from grailed_api import GrailedAPIClient 
from src.models import Listing 
from dataclasses import asdict
from pathlib import Path 
import json 

client = GrailedAPIClient() 

OUTFILE = Path("data/sold/sold_grailed_listings")

def get_sold_products(): 

    products = client.find_products(
        sold=True,
        on_sale=False,
        query_search="chrome hearts"
    )
    
    if products: 
        print("Sample product structure:")
        print(json.dumps(products[0] if isinstance(products, list) else products, indent=2, default=str))
        print() 

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
        listings.append(listing)

        print(f"Listing: {listing.title}")
        print(f" Designer: {listing.designer}")
        print(f" Price: {listing.price}") 
        print(f" Sold Price: {listing.sold_price}") 
        print(f" Size: {listing.size}") 
        print(f" Seller: {listing.seller_name}") 
        print(f" Sold: {listing.sold}")
        print(f" Transactions: {listing.transactions}") 
        print() 

    return listings 

if __name__ == '__main__':
    listings = get_sold_products()
    print(f"Total listings: {len(listings)}")


    


