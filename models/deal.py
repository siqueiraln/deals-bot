from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Deal(BaseModel):
    title: str
    price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[int] = None
    url: str
    affiliate_url: Optional[str] = None
    store: str
    image_url: Optional[str] = None
    timestamp: datetime = datetime.now() # Reminder: This sets time at module load, acceptable for now or fix if critical
    score: float = 0.0
    strategy: Optional[str] = None
