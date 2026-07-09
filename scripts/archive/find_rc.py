import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f: c=f.read()
j=c.find('.result-card')
if j>=0:
    s=c.rfind('\n',0,j-100)
    e=c.find('\n',j+200)
    print(c[s:e])
