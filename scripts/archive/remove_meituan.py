import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
path = os.path.join(base, 'index.html')

with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Remove Meituan CSS ──
# Find exact CSS block to remove: from /* ── Meituan Card Embed ── */ up to but not including /* ── Price trend row + booking icon ── */
# Also remove /* ── 美团增强卡片 ── */ up to /* ── 美团增强卡片 END ── */

css_start = html.find('/* ── Meituan Card Embed ── */')
# Find the next comment or </style>
css_end = html.find('/* ── Price trend row + booking icon ── */', css_start)
if css_start >= 0 and css_end >= 0:
    # Remove the meituan card embed section
    html = html[:css_start] + html[css_end:]
    print(f'Removed Meituan Card Embed CSS (chars {css_start} → {css_end})')

# Now remove the 美团增强卡片 section
mt_enhanced_start = html.find('/* ── 美团增强卡片 ── */')
mt_enhanced_end = html.find('/* ── 美团增强卡片 END ── */', mt_enhanced_start)
if mt_enhanced_start >= 0 and mt_enhanced_end >= 0:
    mt_enhanced_end = mt_enhanced_end + len('/* ── 美团增强卡片 END ── */')
    html = html[:mt_enhanced_start] + html[mt_enhanced_end:]
    print(f'Removed 美团增强卡片 CSS (chars {mt_enhanced_start} → {mt_enhanced_end})')

# ── 2. Remove Meituan Card HTML ──
card_start = html.find('<div class="card" id="meituanCard"')
if card_start >= 0:
    # Find the end of this card (next card or tab-content)
    # The card ends at </div>\n\n<!-- ── Tab： or at the next div.card
    rest = html[card_start:]
    # Find the closing </div> of this card - it's the one before <div class="toast"
    card_end_marker = html.find('<div class="toast"', card_start)
    if card_end_marker >= 0:
        # Go backwards from toast to find the matching </div>
        # Just find the last </div> before toast that closes the meituan card
        # Since the meituan card is: <div class="card" id="meituanCard"> ... </div> \n\n<div class="toast">
        # Find the </div>\n\n<div class="toast" pattern
        pattern = '</div>\n\n<div class="toast"'
        pp = html.find(pattern, card_start)
        if pp >= 0:
            card_end = pp + len('</div>')
            html = html[:card_start] + html[card_end:]
            print(f'Removed Meituan card HTML (chars {card_start} → {card_end})')

# ── 3. Remove Meituan JS functions ──
functions_to_remove = [
    'function toggleMeituan',
    'function meituanSearch',
    'function renderMeituanResult',
    'function formatMeituanData',
    'function injectMeituanCards',
    'function toggleMtCard',
    'function loadMtForCity',
]

for func_name in functions_to_remove:
    idx = html.find(func_name)
    if idx >= 0:
        # Find the closing brace of this function
        depth = 0
        in_func = False
        for pos in range(idx, len(html)):
            if html[pos] == '{':
                depth += 1
                in_func = True
            elif html[pos] == '}':
                depth -= 1
                if in_func and depth == 0:
                    html = html[:idx] + html[pos+1:]
                    print(f'Removed function {func_name} (chars {idx} → {pos+1})')
                    break

# ── 4. Remove postRender wrapper (美团卡片注入) ──
wrapper_marker = '// 包装 postRender（app.js 中定义），渲染后自动注入美团卡片'
idx = html.find(wrapper_marker)
if idx >= 0:
    # Find the closing }); of setTimeout
    end_marker = '},300);'
    end_idx = html.find(end_marker, idx)
    if end_idx >= 0:
        html = html[:idx] + html[end_idx + len(end_marker):]
        print(f'Removed postRender wrapper (chars {idx} → {end_idx + len(end_marker)})')

# ── 5. Remove meituan-related imports from app.py ── (handled separately)

# ── Clean up extra blank lines ──
html = re.sub(r'\n{4,}', '\n\n\n', html)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ index.html 美团移除完毕，新大小: {len(html)} bytes')
print('=' * 50)

# ── Now handle app.py ──
py_path = os.path.join(base, os.pardir, 'app.py')
with open(py_path, 'r', encoding='utf-8') as f:
    py = f.read()

lines = py.split('\n')
py_lines = []

# Track if we're inside a meituan function
skip = False
meituan_function_names = [
    '_save_meituan_cache', '_load_meituan_cache', '_normalize_meituan_city',
    '_preload_meituan_for_city', '_run_meituan_city_query', '_startup_meituan_preload',
    '_trigger_meituan_preload_for_results', '_get_meituan_city_cache',
    '_get_meituan_city_with_parse', '_cleanup_meituan_city_cache', '_run_meituan_query',
]

removed = 0
for line in lines:
    stripped = line.strip()
    
    # Check if this is a meituan function definition
    is_meituan_func = False
    for fn in meituan_function_names:
        if stripped.startswith(f'def {fn}('):
            is_meituan_func = True
            break
    
    if is_meituan_func:
        skip = True
        removed += 1
    
    # Check for meituan route decorators
    is_meituan_route = ('/api/meituan/' in stripped or '/api/meituan' in stripped) and '@' in stripped
    
    if is_meituan_route:
        skip = True
        removed += 1
    
    # Check for meituan constants/global vars
    is_meituan_global = stripped.startswith('MEITUAN_') or stripped == '# _cleanup_meituan_city_cache()'
    
    if is_meituan_global:
        skip = True
        removed += 1
        if stripped.startswith('MEITUAN_CACHE_FILE'):
            skip = True  # skip the next line too
    
    # Skip meituan imports
    if 'meituan_parser' in stripped or 'explore_meituan' in stripped:
        skip = True
        removed += 1
    
    if not skip:
        py_lines.append(line)
    
    # End of a meituan function (next non-indented line that starts a def or @ or is blank)
    if skip:
        # Check if we've reached the end of a function
        if stripped == '' or stripped.startswith('def ') or stripped.startswith('@app.get') or stripped.startswith('@app.api'):
            # We set skip=False, but we need to NOT add the blank line or def/route yet
            skip = False
            # Add the current line (it's a new def/route/blank, not meituan)
            if not is_meituan_route and not is_meituan_func:
                py_lines.append(line)
            continue

# Remove meituan import lines
result = '\n'.join(py_lines)

# Clean up double blank lines
result = re.sub(r'\n{3,}', '\n\n\n', result)

with open(py_path, 'w', encoding='utf-8') as f:
    f.write(result)

print(f'\n✅ app.py 美团移除完毕，新大小: {len(result)} bytes')
print(f'移除行数: {removed}')
