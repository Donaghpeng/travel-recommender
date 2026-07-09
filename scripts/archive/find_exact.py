import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\Donaghy\Desktop\travel-recommender\static')
with open('index.html','r',encoding='utf-8') as f:
    content = f.read()
idx = content.find('</div><!-- /tab-recommend -->')
if idx > -1:
    # Show bytes around it
    snippet = content[idx:idx+90]
    for i, ch in enumerate(snippet):
        print(f'{i:3d}: U+{ord(ch):04X} {repr(ch)}')
