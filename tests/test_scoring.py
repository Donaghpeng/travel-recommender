"""
test_scoring.py — Tests for core scoring functions
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from travel_recommender import (
    score_cost, score_route, score_review, score_weather, score_preference,
    _season_index, _total_estimate
)

# ═══════════════════════════════════════════
# score_cost tests
# ═══════════════════════════════════════════

class TestScoreCost:
    def test_high_budget_returns_high_score(self, cheap_dest):
        s = score_cost(cheap_dest, budget=10000, days=5, si=1, departure="Shanghai")
        assert s >= 4.5, f"Expected high score, got {s}"

    def test_low_budget_returns_low_score(self, beach_dest):
        s = score_cost(beach_dest, budget=1000, days=7, si=2, departure="Shanghai")
        assert s <= 2.0, f"Expected low score, got {s}"

    def test_budget_equal_estimate(self, cheap_dest):
        s = score_cost(cheap_dest, budget=4000, days=5, si=0, departure="Shanghai")
        assert 2.0 <= s <= 5.0, f"Expected 2-5 range, got {s}"

    def test_score_in_valid_range(self, beach_dest):
        s = score_cost(beach_dest, budget=4000, days=3, si=0, departure="Shanghai")
        assert 1.0 <= s <= 5.0, f"Expected 1-5 range, got {s}"


# ═══════════════════════════════════════════
# score_route tests
# ═══════════════════════════════════════════

class TestScoreRoute:
    def test_east_departure_to_east(self, beach_dest):
        beach_dest.region = "East"
        s = score_route(beach_dest, "Shanghai", si=1)
        assert s >= 4.0, f"Expected >=4.0, got {s}"

    def test_international_lower(self, international_dest):
        s = score_route(international_dest, "Shanghai", si=1)
        assert s == 2.5, f"Expected 2.5, got {s}"


# ═══════════════════════════════════════════
# score_review tests
# ═══════════════════════════════════════════

class TestScoreReview:
    def test_high_rating_high_score(self, mountain_dest):
        s = score_review(mountain_dest)
        assert s >= 4.0, f"Expected >=4.0, got {s}"

    def test_score_never_above_5(self, beach_dest):
        s = score_review(beach_dest)
        assert s <= 5.0, f"Expected <=5.0, got {s}"


# ═══════════════════════════════════════════
# score_weather tests
# ═══════════════════════════════════════════

class TestScoreWeather:
    def test_tropical_summer_beach_high(self, beach_dest):
        s = score_weather(beach_dest, month=7)
        assert s >= 3.0, f"Expected >=3.0, got {s}"

    def test_score_range(self, mountain_dest):
        for month in range(1, 13):
            s = score_weather(mountain_dest, month)
            assert 1.0 <= s <= 5.0, f"Month {month}: {s} outside [1,5]"

    def test_weather_data_used_if_available(self, beach_dest):
        s = score_weather(beach_dest, month=1)
        assert s >= 4.0, f"Expected high for January Sanya, got {s}"


# ═══════════════════════════════════════════
# score_preference tests
# ═══════════════════════════════════════════

class TestScorePreference:
    def test_matching_keyword_boosts(self, beach_dest):
        s_no = score_preference(beach_dest, [])
        s_match = score_preference(beach_dest, ["beach"], month=7)
        assert s_match > s_no, f"Expected boosted score, got {s_no} -> {s_match}"

    def test_city_penalty_in_summer(self, beach_dest):
        beach_dest.dest_type = "City"
        s = score_preference(beach_dest, ["city"], month=7)
        assert s >= 1.0, f"Expected >=1.0, got {s}"

    def test_no_prefs_default(self, mountain_dest):
        s = score_preference(mountain_dest, [])
        assert s == 3.0, f"Expected 3.0, got {s}"


# ═══════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════

class TestEdgeCases:
    def test_unknown_type_no_crash(self, beach_dest):
        beach_dest.dest_type = "UnknownType"
        s = score_weather(beach_dest, month=6)
        assert 1.0 <= s <= 5.0

    def test_invalid_date_returns_july(self):
        m = __import__('travel_recommender')._month_from_date
        assert m("2026") == 7
        assert m("not-a-date") == 7
        assert m("2026-03") == 3
