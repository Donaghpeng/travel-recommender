import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
path = os.path.join(base, 'index.html')
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Insert CSS for #poiResults to fix overlapping
css = '\n#poiResults{display:flex;flex-direction:column;gap:0}\n#multiResults{display:flex;flex-direction:column;gap:0}\n'

target = '.tab-content.active{display:block}'
idx = c.find(target)
if idx >= 0:
    end = idx + len(target)
    c = c[:end] + css + c[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'CSS inserted')
    print(f'File size: {len(c)} bytes')
else:
    print('Target not found')
    sys.exit(1)
