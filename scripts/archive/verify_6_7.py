import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'js', 'app.js'), 'r', encoding='utf-8') as f:
    c = f.read()

has_btn = 'poi-to-recommend' in c
has_fn = 'function goToRecommendFromPOI' in c
has_switch = 'switchTab("recommend")' in c
print(f'POI button added: {has_btn}')
print(f'goToRecommendFromPOI: {has_fn}')
print(f'switchTab call: {has_switch}')
print(f'All OK: {has_btn and has_fn and has_switch}')
