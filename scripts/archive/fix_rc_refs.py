import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f:
    c = f.read()

# These functions query .result-card for recommend results (should use .preview-card)
# The 3 functions identified: addBookingButtons, addPriceTrends, showTravelTips
# We need to identify which querySelectorAll(".result-card") calls correspond to these.

# Strategy: find each querySelectorAll(".result-card") WITHOUT #poiResults prefix
# Those within POI functions have "#poiResults" prefix but some don't.
# The easiest approach: replace only the specific 3 occurrences.

# First, let's locate them precisely by function
import re

# Find function boundaries
functions = {}
func_starts = [m.start() for m in re.finditer(r'\nfunction \w+\(', c)]
for i, fs in enumerate(func_starts):
    func_name = c[fs+1:fs+50].split('(')[0].lstrip()
    next_fs = func_starts[i+1] if i+1 < len(func_starts) else len(c)
    functions[func_name] = (fs, next_fs)

target_fns = {'addBookingButtons', 'addPriceTrends', 'showTravelTips'}

for fn_name, (fn_start, fn_end) in functions.items():
    if fn_name not in target_fns:
        continue
    body = c[fn_start:fn_end]
    idx = body.find('.result-card')
    if idx >= 0:
        # Show context for verification
        line_start = body.rfind('\n', 0, idx) + 1
        line_end = body.find('\n', idx)
        print(f'{fn_name}: \"{body[line_start:line_end]}\"')
        # Replace within this function
        abs_idx = fn_start + idx
        old = c[abs_idx:abs_idx+len('.result-card')]
        c = c[:abs_idx] + '.preview-card' + c[abs_idx+len('.result-card'):]
        print(f'  -> replaced at {abs_idx}')

with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
