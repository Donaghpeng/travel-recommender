import json

with open(r'C:\Users\Donaghy\Desktop\travel-recommender\data\result_cache.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Total entries: {}'.format(len(data)))
for d in data:
    key_raw = d.get('key', '')
    items = dict(eval(key_raw))
    dep = items.get('departure', '?')
    ttl = d.get('ttl_remaining', '?')
    print('  - {} (ttl_remaining: {}s)'.format(dep, ttl))
