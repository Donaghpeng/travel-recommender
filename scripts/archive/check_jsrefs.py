import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f: c=f.read()
for kw in ['"good', '"ok"', '"bad"', 'result-card', 'scores-bar', 'sel-circle']:
    i=c.find(kw)
    if i>=0:
        print(f'{kw}: found at {i} -> {c[i:i+60]}')
    else:
        print(f'{kw}: not found')
