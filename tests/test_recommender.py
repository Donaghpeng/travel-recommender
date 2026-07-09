"""
test_recommender.py — Tests for TravelRecommender engine
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from travel_recommender import TravelRecommender


class TestTravelRecommender:
    """Integration tests for the full recommendation pipeline"""

    @pytest.fixture
    def recommender(self):
        return TravelRecommender()

    def test_recommender_has_destinations(self, recommender):
        """Should have 126 destinations loaded"""
        assert len(recommender.destinations) == 126, \
            f"Expected 126, got {len(recommender.destinations)}"

    def test_recommend_returns_5_results(self, recommender):
        """Default recommend should return 5 results"""
        inp = {
            "budget": 4000, "days": 5, "travel_date": "2026-07",
            "departure": "Shanghai", "preferences": ["beach", "food"],
            "travelers": "couple", "region": "all"
        }
        results = recommender.recommend(inp)
        assert len(results) == 5, f"Expected 5, got {len(results)}"

    def test_results_have_required_fields(self, recommender):
        """Each result should have core fields"""
        inp = {"budget": 4000, "days": 3, "travel_date": "2026-07",
               "departure": "Shanghai", "preferences": [], "travelers": "solo", "region": "all"}
        results = recommender.recommend(inp)
        for r in results:
            assert "name" in r, f"Missing name: {r}"
            assert "total_score" in r
            assert "scores" in r
            assert "cost" in r["scores"]
            assert "weather" in r["scores"]
            assert "estimate" in r
            assert "type" in r
            assert "latitude" in r
            assert "longitude" in r

    def test_scores_in_range(self, recommender):
        """All scores should be 1.0-5.0"""
        inp = {"budget": 5000, "days": 4, "travel_date": "2026-06",
               "departure": "Beijing", "preferences": ["nature"],
               "travelers": "friends", "region": "all"}
        results = recommender.recommend(inp)
        for r in results:
            for dim, val in r["scores"].items():
                assert 1.0 <= val <= 5.0, f"{r['name']}.{dim} = {val}"

    def test_results_are_diversified(self, recommender):
        """Results should not be all same type"""
        inp = {"budget": 4000, "days": 5, "travel_date": "2026-07",
               "departure": "Shanghai", "preferences": ["beach"],
               "travelers": "solo", "region": "all"}
        results = recommender.recommend(inp)
        types = set(r["type"] for r in results)
        assert len(types) >= 2, f"Only 1 type: {types}"

    def test_domestic_filter(self, recommender):
        """region=domestic should only return China destinations"""
        inp = {"budget": 4000, "days": 5, "travel_date": "2026-07",
               "departure": "Shanghai", "preferences": [],
               "travelers": "solo", "region": "domestic"}
        results = recommender.recommend(inp)
        for r in results:
            assert r["country"] == "China", f"{r['name']} not China"

    def test_international_filter(self, recommender):
        """region=international should only return non-China destinations"""
        inp = {"budget": 8000, "days": 5, "travel_date": "2026-07",
               "departure": "Shanghai", "preferences": [],
               "travelers": "solo", "region": "international"}
        results = recommender.recommend(inp)
        for r in results:
            assert r["country"] != "China", f"{r['name']} is China"
