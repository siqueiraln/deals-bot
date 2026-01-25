"""
Category-based deduplication for deals.
Ensures diversity by limiting how many products from each category appear per cycle.
"""

from typing import List, Dict
from models.deal import Deal
import re

def detect_category(title: str) -> str:
    """
    Detect product category from title using keyword matching.
    
    Args:
        title: Product title
        
    Returns:
        Category name or "outros" if no match
    """
    title_lower = title.lower()
    
    # Category keywords (order matters - more specific first)
    category_keywords = {
        "notebook": ["notebook", "laptop"],
        "celular": ["celular", "smartphone", "iphone", "galaxy", "xiaomi", "redmi", "poco"],
        "tablet": ["tablet", "ipad"],
        "monitor": ["monitor"],
        "relogio": ["relogio", "relógio", "smartwatch", "watch"],
        "fone": ["fone", "headset", "earbuds", "airpods", "buds"],
        "tenis": ["tenis", "tênis", "sneaker"],
    }
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in title_lower:
                return category
    
    return "outros"

def deduplicate_by_category(deals: List[Deal], category_limits: Dict[str, int]) -> List[Deal]:
    """
    Deduplicate deals by category, keeping only top N per category based on score.
    
    Args:
        deals: List of deals with scores
        category_limits: Dict mapping category name to max count
        
    Returns:
        Filtered list of deals with category diversity
    """
    # Group deals by category
    categories = {}
    for deal in deals:
        category = detect_category(deal.title)
        if category not in categories:
            categories[category] = []
        categories[category].append(deal)
    
    # Sort each category by score (descending)
    for category in categories:
        categories[category].sort(key=lambda d: d.score, reverse=True)
    
    # Apply limits
    result = []
    for category, category_deals in categories.items():
        limit = category_limits.get(category, category_limits.get("outros", 3))
        result.extend(category_deals[:limit])
    
    # Sort final result by score
    result.sort(key=lambda d: d.score, reverse=True)
    
    return result
