import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'js', 'app.js'), 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('function renderPOIResults')
end = c.find('\nfunction', idx+1)
lines = c[idx:end].split('\n')

# Find all html += lines with div opens/closes
for i, line in enumerate(lines):
    if 'html += ' in line and ('</div>' in line or '<div' in line):
        print(f'L{idx+i}: {line}')
    elif 'poi-to-recommend' in line or 'goToRecommendFromPOI' in line:
        print(f'L{idx+i}: {line}')
