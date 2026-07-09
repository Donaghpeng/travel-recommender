import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8') as f:
    content = f.read()

opens = len(re.findall(r'<div\b', content))
closes = len(re.findall(r'</div>', content))
print(f'div opens: {opens}')
print(f'div closes: {closes}')
if opens == closes:
    print('Balance: OK')
else:
    print(f'Balance: MISMATCH diff={opens-closes}')

for m in re.finditer(r'<div class="tab-content[^"]*"[^>]*>', content):
    tag = m.group()
    pos = m.start()
    print(f'\nTab at {pos}: {tag}')
    if 'tab-recommend' in tag:
        close = content.find('<!-- /tab-recommend -->', pos)
        print(f'  Closes at {close}')
        after_close = content[close:close+100]
        print(f'  After close: {repr(after_close)}')
    else:
        close = content.find('</div>', pos + len(tag))
        close2 = content.find('</div>', close + 6)
        print(f'  Content ends at {close2}')
