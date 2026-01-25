from dataclasses import dataclass

@dataclass
class TrendingTerm:
    term: str
    category: str
    trend_type: str  # "crescimento", "desejado", "popular"
    rank: int
    url: str
