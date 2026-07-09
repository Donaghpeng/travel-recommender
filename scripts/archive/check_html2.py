import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\Donaghy\Desktop\travel-recommender\static')
with open('index.html','r',encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
for i, line in enumerate(lines):
    s = line.strip()
    # Remove emoji for printing
    clean = re.sub(r'[^\x20-\x7E\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '?', s)
    if any(k in s for k in ['tab-', 'id="results"', '/tab-recommend', 'footer', '</div>']):
        if len(clean) > 5:
            print(f'{i:4d}: {clean[:90]}')
