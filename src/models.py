from dataclasses import dataclass
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
    date_sold: Optional[str] = None


@dataclass(frozen=True)
class ComparableSearchCriteria:
    """Everything needed to search sold listings for one active listing:
    cleaned title query plus the structured fields (category, size) that
    narrow the search itself, rather than filtering results afterward."""
    query: str
    category: str = ""
    size: str = ""


@dataclass(frozen=True)
class MarketComparable:
    """A single sold listing used as a comparable for market valuation."""
    listing_id: str
    title: str
    sold_price: float
    date_sold: Optional[str]
    similarity_score: float
    recency_weight: float
    weight: float


@dataclass(frozen=True)
class MarketValuation:
    """Estimated market value for an active listing, from weighted comparables."""
    listing_id: str
    estimated_value: Optional[float]
    confidence: float
    comparables: tuple = ()


@dataclass(frozen=True)
class DealCriteria:
    """Hard filter thresholds and scoring config for deal evaluation."""
    min_discount_pct: float = 0.30
    min_seller_rating: float = 3.0
    min_transactions: int = 1
    max_listing_age_days: int = 180
    require_buynow: bool = True
    require_makeoffer: bool = True
    title_similarity_threshold: float = 0.6


@dataclass(frozen=True)
class DealScore:
    """Composite deal score for an active listing against a market valuation."""
    listing_id: str
    discount_score: float
    seller_score: float
    urgency_score: float
    demand_score: float
    composite_score: float
    passes_hard_filters: bool
    fail_reasons: tuple = ()
