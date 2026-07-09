import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'js', 'app.js'), 'r', encoding='utf-8') as f:
    c = f.read()

# Find the main search trigger function
search_markers = ['function doSearch', 'function searchRecommend', 'searchBtn']
for marker in search_markers:
    i = c.find(marker)
    if i >= 0:
        line_start = c.rfind('\n', 0, i) + 1
        print(f'\n=== {marker} at {i} ===')
        print(c[line_start:line_start+500])
    else:
        print(f'{marker}: not found')
