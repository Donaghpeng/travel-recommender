import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('<style>')
if idx < 0:
    idx = c.find('/* CSS Variables')
    if idx < 0:
        print('No style tag found')
        sys.exit(1)
end = c.find('</style>', idx)

# Show CSS that affects .result-card and related styles
lines = c[idx:end].split('\n')
for i, line in enumerate(lines):
    if any(kw in line for kw in ['.result-card', '#poiResults', '.poi-', '.preview-', 'display:flex', 'flex-wrap', '.tab-content .card']):
        print(f'L{i}: {line}')
