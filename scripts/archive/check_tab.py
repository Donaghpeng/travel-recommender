import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\Donaghy\Desktop\travel-recommender\static')
with open('index.html','r',encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
for i in range(340, 370):
    s = lines[i]
    clean = re.sub(r'[^\x20-\x7E\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '?', s)
    print(f'{i:4d}: {clean}')
