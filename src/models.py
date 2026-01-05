from dataclasses import dataclass 
from token import OP
from typing import Optional 
from datetime import datetime 

@dataclass (frozen=True)
class Listing: 
    """Class for defining listing fields."""
    listing_id: Optional[str] = None
    title: Optional[str] = None
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


@dataclass (frozen=True) 
class Listing_API:
    """Class for products on Grailed API""" 
    created_at: Optional[str] = None 
    designer: Optional[str] = None 
    updated_price: Optional[str] = None 
    price: Optional[float] = None 
    date_sold: Optional[str] = None 
    sold: Optional[bool] = None 
    price_drops: Optional[str] = None 
    price_i: Optional[str] = None 
    price_updated_at_i: Optional[int] = None 
    size: Optional[str] = None 
    username: Optional[str] = None 
    total_bought_and_sold: Optional[int] = None 
    seller_score: Optional[str] = None 
    rating_average: Optional[str] = None 
    rating_count: Optional[str] = None 
    trusted_seller: Optional[str] = None 
    sold_price: Optional[int] = None 
    department: Optional[str] = None 
    title: Optional[str] = None     
    



