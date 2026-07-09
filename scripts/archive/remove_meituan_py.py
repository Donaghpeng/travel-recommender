import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender'
path = os.path.join(base, 'app.py')

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove all lines that are meituan-related
new_lines = []
skip_block = False
removed = 0

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Detect start of a meituan block
    is_meituan_start = False

    # Meituan constant definitions
    if stripped.startswith('MEITUAN_'):
        is_meituan_start = True
    
    # Meituan route decorators  
    if stripped.startswith('@app.get("/api/meituan') or stripped.startswith('@app.api_route("/api/meituan'):
        is_meituan_start = True

    # Meituan function definitions
    if stripped in ['def _save_meituan_cache():', 'def _load_meituan_cache():',
                     'def _normalize_meituan_city(city_name: str) -> str:',
                     'def _preload_meituan_for_city(city_name: str):',
                     'def _run_meituan_city_query(city_key: str, q: str, city: str):',
                     'def _startup_meituan_preload():',
                     'def _trigger_meituan_preload_for_results(results: list):',
                     'def _get_meituan_city_cache(city_name: str):',
                     'def _get_meituan_city_with_parse(city_name: str):',
                     'def _cleanup_meituan_city_cache():',
                     'def _run_meituan_query(task_id: str, q: str, city: str):']:
        is_meituan_start = True

    # Meituan route definitions
    for route_prefix in ['def meituan_query_start', 'def meituan_result(', 'def meituan_cleanup(',
                          'def meituan_cached(', 'def meituan_cache_status(', 'def meituan_preload(',
                          'def meituan_preload_status(', 'def meituan_kill(', 'def meituan_kill_all(',
                          'async def meituan_status(']:
        if stripped.startswith(route_prefix):
            is_meituan_start = True
            break

    # Commented-out meituan calls
    if '# _cleanup_meituan' in stripped or '# _load_meituan_cache()' in stripped or '_meituan_preload' in stripped:
        is_meituan_start = True

    # Import lines
    if 'explore_meituan' in stripped or 'meituan_parser' in stripped:
        is_meituan_start = True

    if is_meituan_start:
        skip_block = True

    if not skip_block:
        new_lines.append(line)
    
    # When we encounter a blank line or new def/route after a block, stop skipping
    if skip_block:
        # Check if we've reached a clear new definition
        if (stripped == '' or stripped.startswith('def ') or stripped.startswith('@app.')):
            if not is_meituan_start:  # don't stop on the triggering line
                skip_block = False
                # Add this line if it's not meituan
                if not stripped.startswith('def meituan_') and not stripped.startswith('@app.get("/api/meituan'):
                    new_lines.append(line)
        i += 1
        continue

    i += 1

result = ''.join(new_lines)

# Clean up excessive blank lines
import re
result = re.sub(r'\n{4,}', '\n\n\n', result)

with open(path, 'w', encoding='utf-8') as f:
    f.write(result)

print(f'app.py 新大小: {len(result)} bytes')
print(f'原行数: {len(lines)}, 新行数: {len(new_lines)}')
