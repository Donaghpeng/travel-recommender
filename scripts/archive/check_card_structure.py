import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'js', 'app.js'), 'r', encoding='utf-8') as f:
    c = f.read()

# Find renderPOIResults and show the card-building section
idx = c.find('function renderPOIResults')
end = c.find('\nfunction', idx+1)

# Show the card HTML building part - look for the closings
lines = c[idx:end].split('\n')
for i, line in enumerate(lines):
    if 'html +=' in line or 'poi-to-recommend' in line or 'resEl.innerHTML' in line:
        print(f'{i:4d}: {line}')
