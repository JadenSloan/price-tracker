import re 
import json
from pathlib import Path

# remove sizes, condition, color, price tokens, marketing fluff, 
# standardize brand aliases 

# Loop through the title in grailed.listings.JSON
# Add filters 
BRAND_ALIASES = {
    "ch": "chrome hearts",
}

JUNK_PHRASES = [
    r"rare",
]

def clean_title(title):
    title = title.lower() 

    title = re.sub(r"[^\w\s]", "", title) 
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"\b(size|sz|s|m|l|xl)\b", "", title, flags=re.I)  

    # Replace brand aliases (e.g., "ch" -> "Chrome Hearts")
    for alias, replacement in BRAND_ALIASES.items(): 
        title = re.sub(rf'\b{re.escape(alias)}\b', replacement, title, re.IGNORECASE)
    
    # Remove junk phrases
    for phrase in JUNK_PHRASES: 
        title = re.sub(rf'\b{re.escape(phrase)}\b', "", title, flags=re.IGNORECASE)  

    return title 


def main(): 
    # Load JSON from data folder
    with open('data/grailed_listings.json', 'r') as f: 
        data = json.load(f) 

    for listing in data: 
        if "title" in listing: 
            listing["title"] = clean_title(listing["title"]) 

    output_path = Path("data/grailed_listings_clean.json") 
    output_path.write_text(json.dumps(data, indent=2))  
    print(f"Saved {len(data)} listings to {output_path.resolve()}")  

if __name__ == "__main__":
    main() 
    
    