"""
conftest.py — Shared test fixtures for travel recommender tests
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from travel_recommender import Destination, _season_index, _month_from_date

# ─── Sample Destination Fixtures ──────────────────────────

@pytest.fixture
def beach_dest():
    return Destination(
        id=1, name="Sanya", country="China", region="South", dest_type="Beach",
        latitude=18.25, longitude=109.51,
        description="Tropical beach city",
        keywords=["beach", "vacation", "diving", "tropical"],
        cost_flight=(800, 1200, 2000),
        cost_hotel_per_night=(200, 350, 600),
        cost_food_per_day=(100, 150, 200),
        cost_ticket=200,
        cost_local_transport=(50, 80, 100),
        rating_overall=4.3, rating_count=50000,
        weather={
            1: (27,20,15,4.5), 4: (32,25,20,4.3),
            7: (33,26,180,3.0), 10: (31,24,60,4.0),
        }
    )

@pytest.fixture
def mountain_dest():
    return Destination(
        id=2, name="Huangshan", country="China", region="East", dest_type="Mountain",
        latitude=30.13, longitude=118.17,
        description="Yellow Mountain, famous for its scenery",
        keywords=["mountain", "nature", "photography", "hiking"],
        cost_flight=(500, 700, 1200),
        cost_hotel_per_night=(100, 200, 350),
        cost_food_per_day=(60, 100, 150),
        cost_ticket=190,
        cost_local_transport=(30, 50, 70),
        rating_overall=4.5, rating_count=45000,
    )

@pytest.fixture
def international_dest():
    return Destination(
        id=3, name="Bangkok (Thailand)", country="Thailand", region="SE Asia", dest_type="City",
        latitude=13.76, longitude=100.50,
        description="Capital of Thailand, vibrant city",
        keywords=["city", "food", "culture", "shopping", "temple"],
        cost_flight=(800, 1200, 2000),
        cost_hotel_per_night=(150, 250, 400),
        cost_food_per_day=(60, 100, 150),
        cost_ticket=0,
        cost_local_transport=(30, 50, 80),
        rating_overall=4.2, rating_count=60000,
    )

@pytest.fixture
def cheap_dest():
    return Destination(
        id=4, name="Guilin", country="China", region="South", dest_type="Nature",
        latitude=25.28, longitude=110.29,
        description="Famous for karst landscape",
        keywords=["nature", "photography", "hiking", "river"],
        cost_flight=(300, 500, 900),
        cost_hotel_per_night=(60, 100, 200),
        cost_food_per_day=(40, 70, 100),
        cost_ticket=80,
        cost_local_transport=(20, 30, 50),
        rating_overall=4.1, rating_count=25000,
    )

# ─── Helper fixtures ──────────────────────────────────────

@pytest.fixture(params=[1, 4, 7, 10])
def sample_month(request):
    """January, April, July, October"""
    return request.param

@pytest.fixture(params=["Shanghai", "Beijing", "Guangzhou"])
def departure_city(request):
    return request.param
