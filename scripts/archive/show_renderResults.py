import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f: c=f.read()

# Show renderResults function content
i=c.find('function renderResults')
j=c.find('function renderDrawer', i)
if j<0: j=c.find('\nfunction ', i+10)

print(c[i:j])
