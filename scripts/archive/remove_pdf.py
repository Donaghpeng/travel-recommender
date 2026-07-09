import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static\js'
path = os.path.join(base, 'app.js')

with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('function _pdfRemoved')
if idx < 0:
    idx = js.find('function generatePDF')
if idx < 0:
    print('NOT FOUND')
    exit()

depth = 0
in_func = False
end = idx
for pos in range(idx, len(js)):
    if js[pos] == '{':
        depth += 1
        in_func = True
    elif js[pos] == '}':
        depth -= 1
        if in_func and depth == 0:
            end = pos + 1
            break

print('Removing chars', idx, 'to', end)
js = js[:idx] + js[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(js)
print('New size:', len(js))
print('generatePDF in file:', 'generatePDF' in js)
