import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('compare-bar')
if idx >= 0:
    start = max(0, idx - 300)
    end = min(len(c), idx + 300)
    # Find nearest line breaks
    s = c.rfind('\n', 0, start) + 1
    e = c.find('\n', end)
    if e < 0: e = len(c)
    print(c[s:e])
else:
    print('compare-bar not found in JS')
