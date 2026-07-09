import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('<style>')
end = c.find('</style>', idx)

# Show all CSS
lines = c[idx:end].split('\n')
for i, line in enumerate(lines, 1):
    if line.strip():
        print(f'{i:4d}: {line.rstrip()}')
