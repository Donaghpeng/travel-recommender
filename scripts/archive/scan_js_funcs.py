import re, os
os.chdir(r"C:\Users\Donaghy\Desktop\travel-recommender")
with open('static/js/app.js','r',encoding='utf-8') as f:
    content = f.read()

# Find all function definitions
funcs = re.findall(r'(?:^|\n)(?:function |var )?(\w+)\s*[=\(]', content)
print("=== Key functions ===")
for f_name in funcs:
    if any(k in f_name for k in ['render','search','show','POI','poi','Search','modal','compare','multi','export']):
        idx = content.find(f_name)
        line = content[:idx].count('\n') + 1
        print(f"  Line {line:5d}: {f_name}")

print("\n=== POI-related sections ===")
pat = r'(poiSearch|renderPoi|poiPaginat|openPoi|showPoi)'
matches = list(re.finditer(pat, content, re.IGNORECASE))
for m in matches:
    line = content[:m.start()].count('\n') + 1
    print(f"  Line {line}: ...{m.group()}...")
