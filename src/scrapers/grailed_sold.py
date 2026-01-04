import requests 
from pathlib import Path 
import json 
from src.models import Listing 
from dataclasses import asdict 


ALGOLIA_APP_ID = "MNRWEFSS2Q" 
ALGOLIA_API_KEY = "" 
ALGOLIA_INDEX = "Listing_production" 

def fetch_sold_listings(designer="chrome hearts", max_pages=50): 
    """Fetch sold listings directly from Algolia API""" 
    url = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/net/1/indexes/{ALGOLIA_INDEX}/query" 

    headers = {
        "x-algolia-agent": "Algolia for JavaScript (4.14.2); Browser",
        "x-algolia-api-key": ALGOLIA_API_KEY,
        "x-algolia-application-id": ALGOLIA_APP_ID,
        "Content-Type": "application/json"  
    }

    all_listings = []

    for page in range(max_pages): 
        payload = {
            "query": designer, 
            "page": page, 
            "hitsPerPage": 100, 
            "filters": f"sold:true AND designers: {designer}" 
        }

        response = requests.post(url, headers=headers, json=payload) 
        data = response.json() 
        hits = data.get("hits", []) 

        if not hits: 
            break 

        # Map Algolia hits to Listin model 
        for hit in hits: 
            listing = Listing( 
                listing_id=str(hit.get("objectID")),
                title=hit.get("title"),
                price=hit.get("price"),
                sold_price=hit.get("sold_price")
                # ... map other fields 
            ) 
            all_listings.append(asdict(listing)) 

        print(f"Page {page}: fetched {len(hits)} listings")
    
    # Save to data/sold/ 
    output = Path("data/sold/grailed_sold.json") 
    output.write_text(json.dumps(all_listings, indent=2)) 
    print(f"Total: {len(all_listings)} sold listings")
    return all_listings 
    