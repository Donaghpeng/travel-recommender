import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
path = os.path.join(base, 'index.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find boundaries using actual content
poi_comment = '<!-- \u2500\u2500 Tab\uff1a\u666f\u70b9\u63a2\u7d22 \u2500\u2500 -->'
rec_comment = '<!-- /tab-recommend -->'
mt_comment = '<!-- \u7f8e\u56e2\u67e5\u8be2\u5361\u7247'

old_start = content.find(poi_comment)
if old_start < 0:
    print('ERROR: Could not find POI comment')
    sys.exit(1)

old_end = content.find(rec_comment)
if old_end < 0:
    print('ERROR: Could not find /tab-recommend comment')
    sys.exit(1)
old_end += len(rec_comment)

mt_idx = content.find(mt_comment, old_start)
if mt_idx < 0:
    print('ERROR: Could not find meituan comment')
    sys.exit(1)

# Split: POI+multi tabs (old_start to mt_idx) vs remaining (mt_idx to old_end)
poi_multi_part = content[old_start:mt_idx]
remaining_part = content[mt_idx:old_end]

# Rearrange: remaining first, then POI+multi
new_block = remaining_part + '\n\n' + poi_multi_part

new_content = content[:old_start] + new_block + content[old_end:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Done! {len(content)} -> {len(new_content)} bytes')
print(f'POI+multi part: {len(poi_multi_part)} bytes')
print(f'Remaining part: {len(remaining_part)} bytes')
