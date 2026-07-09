import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f: c=f.read()
i=c.find('"good"')
if i>=0:
    s=c.rfind('\n',0,i)
    e=c.find('\n',i+200)
    print(c[s:e])
    print('---')
# Also find result-card reference
i=c.find('result-card')
if i>=0:
    s=c.rfind('\n',0,i)
    e=c.find('\n',i+200)
    print(c[s:e])
