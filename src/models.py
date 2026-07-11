"""
models.py — 评价数据模型定义
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Review:
    id: str
    destination: str
    user: str
    rating: float          # 1.0 - 5.0
    content: str
    date: str              # "2026-06"
    traveler_type: str     # solo / couple / family / friends
    budget_range: str      # "3000-5000"
    tags: list[str] = field(default_factory=list)
    photos: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


@dataclass
class ReviewStats:
    destination: str
    avg_rating: float = 0.0
    total_count: int = 0
    distribution: dict = field(default_factory=lambda: {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0})
    keyword_tags: list[dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
