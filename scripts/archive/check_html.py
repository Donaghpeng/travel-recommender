import os
os.chdir(r'C:\Users\Donaghy\Desktop\travel-recommender\static')
with open('index.html','r',encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
for i, line in enumerate(lines):
    s = line.strip()
    if any(k in s for k in ['tab-', 'id="results"', '/tab-recommend']):
        print(f'{i:4d}: {s[:90]}')
