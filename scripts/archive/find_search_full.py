import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'js', 'app.js'), 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('document.getElementById("searchBtn")')
end = c.find('\nfunction', idx)
if end < 0:
    end = idx + 3000
print(c[idx:end])
