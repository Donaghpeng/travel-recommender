import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f: c=f.read()

import re
for m in re.finditer(r'.result-card.', c):
    s=c.rfind('\n',0,m.start()) + 1
    e=c.find('\n',m.end())
    # Get function context
    fn_s = c.rfind('\nfunction ', 0, m.start())
    fn_name = c[fn_s+1:fn_s+50].split('(')[0] if fn_s >= 0 else 'unknown'
    print(f'--- At {m.start()} (in {fn_name}) ---')
    print(c[s:e])
