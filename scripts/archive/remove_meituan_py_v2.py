import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender'
path = os.path.join(base, 'app.py')

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define patterns that mark the start of a meituan block
meituan_triggers = [
    # Constants
    r'^MEITUAN_',
    # Commented startup calls
    r'^    #         _cleanup_meituan_city_cache',
    r'^    # _load_meituan_cache',
    r'^    # threading\.Thread\(target=_startup_meituan_preload',
    # Imports
    r'from explore_meituan',
    r'from meituan_parser',
    # Function defs (must be at line start or with 0 indent)
    r'^def _save_meituan_cache',
    r'^def _load_meituan_cache',
    r'^def _normalize_meituan_city',
    r'^def _preload_meituan_for_city',
    r'^def _run_meituan_city_query',
    r'^def _startup_meituan_preload',
    r'^def _trigger_meituan_preload_for_results',
    r'^def _get_meituan_city_cache',
    r'^def _get_meituan_city_with_parse',
    r'^def _cleanup_meituan_city_cache',
    r'^def _run_meituan_query',
    # Route defs
    r'^def meituan_query_start',
    r'^def meituan_result',
    r'^def meituan_cleanup',
    r'^def meituan_cached',
    r'^def meituan_cache_status',
    r'^def meituan_preload',
    r'^def meituan_preload_status',
    r'^def meituan_kill',
    r'^def meituan_kill_all',
    r'^async def meituan_status',
    # Route decorators
    r'^@app\.get\("/api/meituan',
    r'^@app\.api_route\("/api/meituan',
]

lines = content.split('\n')
result = []
skip = False

for line in lines:
    stripped = line.strip()
    
    # Check if any trigger matches
    triggered = False
    for pattern in meituan_triggers:
        if re.match(pattern, line):
            triggered = True
            break
    
    # Also check inline code references (already inside skipped block - handled by skip state)
    
    if triggered:
        skip = True
        # Don't add this line
    
    if not skip:
        # Even if not skipping, check if line contains meituan references (leftover vars)
        # Only skip meituan constant access lines inside functions we couldn't fully remove
        if 'MEITUAN_' in line or '_meituan_' in line:
            # Check if this is clearly inside a meituan function body (starts with whitespace)
            if line.startswith(' ') or line.startswith('\t'):
                skip = True  # It's inside a meituan block, skip it
                continue
        result.append(line)
    
    # End skip when we hit a blank line or next def/router
    if skip and (stripped == '' or stripped.startswith('def ') or stripped.startswith('@app.')):
        if not triggered:
            skip = False
            if not stripped == '':
                # Add the non-meituan line
                # But first check it's not still meituan-related
                ok = True
                for pattern in meituan_triggers:
                    if re.match(pattern, line):
                        ok = False
                        skip = True
                        break
                if ok:
                    result.append(line)

output = '\n'.join(result)

# Clean excessive blank lines
output = re.sub(r'\n{4,}', '\n\n\n', output)

with open(path, 'w', encoding='utf-8') as f:
    f.write(output)

# Verify
remaining = output.lower().count('meituan')
print(f'Remaining meituan mentions: {remaining}')
if remaining:
    for i, line in enumerate(output.split('\n'), 1):
        if 'meituan' in line.lower():
            print(f'  L{i}: {line}')
else:
    print('✅ All clean!')

print(f'\nFile size: {len(output)} bytes')
print(f'Lines: {len(output.split(chr(10)))}')
