import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find compare-bar in body
idx = c.find('class="compare-bar"')
if idx >= 0:
    print('Compare bar HTML at', idx)
    print(c[max(0,idx-200):idx+300])
    print('===')
else:
    print('compare-bar not found in body')

# Find toggleSelect  
idx = c.find('function toggleSelect')
if idx >= 0:
    print('toggleSelect at', idx)
    print(c[idx:idx+500])
else:
    print('toggleSelect not found')
