import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
path = os.path.join(base, 'index.html')

with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Find all meituan sections
markers = []

# CSS
idx = html.find('/* ── Meituan Card Embed ── */')
if idx >= 0:
    end = html.find('/* ── Reviews ── */', idx)
    markers.append(('CSS', idx, end))

# HTML
idx = html.find('<div class="card" id="meituanCard"')
if idx >= 0:
    # Find next card or tab-content
    next_marker = html.find('<div class="card"', idx + 1)
    if next_marker < 0:
        next_marker = html.find('tab-content', idx + 1)
    markers.append(('HTML', idx, next_marker))

# JS functions
# Find each relevant function
for func in ['toggleMeituan', 'meituanSearch', 'renderMeituanResult', 'formatMeituanData', 'injectMeituanCards']:
    idx = html.find(f'function {func}')
    if idx >= 0:
        # Find closing brace
        depth = 0
        in_func = False
        for pos in range(idx, len(html)):
            if html[pos] == '{':
                depth += 1
                in_func = True
            elif html[pos] == '}':
                depth -= 1
                if in_func and depth == 0:
                    markers.append(('JS:' + func, idx, pos + 1))
                    break

for name, start, end in sorted(markers, key=lambda x: x[1]):
    print(f'{name}: chars {start} → {end}')
    excerpt = html[start:min(end, start+120)].replace('\n', '\\n')
    print(f'  {excerpt}')
    print()
