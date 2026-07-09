import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8') as f:
    content = f.read()

# Find container
idx1 = content.find('<div class="container">')
idx2 = content.find('</div>', idx1+30)
print('Container open:')
print(repr(content[idx1:idx2+50]))

# Count tab-content divs and their nesting
tab_starts = [m.start() for m in re.finditer(r'<div class="tab-content', content)]
tab_ends = [m.start() for m in re.finditer(r'/tab-recommend', content)]
print(f'\nTab-content starts at positions: {tab_starts}')
print(f'/tab-recommend at positions: {tab_ends}')

# Show each tab-content's opening
for pos in tab_starts:
    end_gt = content.index('>', pos)
    print(f'\nTab at {pos}: {content[pos:end_gt+1]}')
    # Show next 300 chars
    print(f'  Next 300: {repr(content[end_gt+1:end_gt+301])}')
