import sys, time
sys.path.insert(0, r'C:\Users\Donaghy\Desktop\travel-recommender')
from app import _get

print('Testing _get for 上海...', flush=True)
t0 = time.time()
result = _get({
    'budget': 4000, 'days': 5,
    'travel_date': '2026-07', 'departure': '上海',
    'preferences': ['海滩', '美食'], 'travelers': '情侣', 'region': 'all',
})
t = time.time() - t0
print('Completed in {:.3f}s with {} results'.format(t, len(result)), flush=True)
for r in result[:3]:
    print('  - {} ({})'.format(r['name_cn'], r['total_score']), flush=True)
