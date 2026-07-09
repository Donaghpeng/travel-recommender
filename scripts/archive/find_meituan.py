import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender'

# --- app.py ---
with open(os.path.join(base, 'app.py'), 'r', encoding='utf-8') as f:
    py = f.read()

# Find Meituan routes
py_lines = py.split('\n')
print("=== app.py 美团相关 ===")
for i, line in enumerate(py_lines, 1):
    if 'meituan' in line.lower() or 'mei_tuan' in line.lower() or 'mt' == line.lower().strip()[:2]:
        print(f'  L{i}: {line}')
print()

# --- app.js ---
with open(os.path.join(base, 'static', 'js', 'app.js'), 'r', encoding='utf-8') as f:
    js = f.read()

js_lines = js.split('\n')
print("=== app.js 美团相关 ===")
count = 0
for i, line in enumerate(js_lines, 1):
    if 'meituan' in line.lower() or 'meiTuan' in line or 'mtCard' in line or 'toggleMt' in line or 'loadMt' in line or 'formatMeituan' in line or 'injectMeituan' in line or 'meituanSearch' in line or 'toggleMeituan' in line:
        count += 1
        if count <= 30:
            print(f'  L{i}: {line}')
print(f'  ... total {count} lines')
print()

# --- index.html ---
with open(os.path.join(base, 'static', 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

html_lines = html.split('\n')
print("=== index.html 美团相关 ===")
count = 0
for i, line in enumerate(html_lines, 1):
    if 'meituan' in line.lower() or 'mtCard' in line or 'meituan_card' in line or 'mt-btn' in line:
        count += 1
        if count <= 20:
            print(f'  L{i}: {line}')
print(f'  ... total {count} lines')
