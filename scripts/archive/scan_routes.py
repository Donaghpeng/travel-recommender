import re, os

os.chdir(r"C:\Users\Donaghy\Desktop\travel-recommender")
with open('app.py','r',encoding='utf-8') as f:
    content = f.read()

routes = re.findall(r'@app\.(get|post)\("([^"]+)"', content)
print('=== All API Routes ===')
for method, path in routes:
    print(f'  {method.upper():6s} {path}')
print(f'\nTotal: {len(routes)} routes')
