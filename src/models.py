from dataclasses import dataclass 
from typing import Optional 
from datetime import datetime 

@dataclass (frozen=True)
class Listing: 
    """Class for defining listing fields."""
    listing_id: str
    title: str
    price: Optional[float] = None 
    size: Optional[str] = None 
    listing_url: Optional[str] = None 
    posted_time: Optional[datetime] = None  
    bumped_time: Optional[datetime] = None  
    seller_name: Optional[str] = None 
    seller_rating: Optional[float] = None 
    rating_count: Optional[int] = None 
    location: Optional[str] = None 
    designer: Optional[str] = None 
    condition: Optional[str] = None 
    image_url: Optional[str] = None 
    sold_price: Optional[float] = None 
    transactions: Optional[int] = None 
    category: Optional[str] = None 
    buynow: Optional[bool] = None 
    makeoffer: Optional[bool] = None 
    sold: Optional[bool] = None 


    
    



