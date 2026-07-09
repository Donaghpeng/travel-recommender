import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f:
    c = f.read()

targets = [
    'addBookingButtons',
    'addPriceTrends',
    'showTravelTips',
]

for fn_name in targets:
    fn_start = c.find('function ' + fn_name)
    if fn_start < 0:
        print(f'{fn_name}: function not found')
        continue
    fn_end = c.find('\nfunction ', fn_start + 10)
    if fn_end < 0: fn_end = len(c)
    fn_body = c[fn_start:fn_end]
    idx = fn_body.find('.result-card')
    if idx >= 0:
        abs_idx = fn_start + idx
        c = c[:abs_idx] + '.preview-card' + c[abs_idx + len('.result-card'):]
        print(f'{fn_name}: replaced at {abs_idx}')
    else:
        print(f'{fn_name}: no result-card found')

with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
