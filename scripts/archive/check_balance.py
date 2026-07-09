import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\Donaghy\Desktop\travel-recommender\static')
with open('index.html','r',encoding='utf-8') as f:
    content = f.read()
opens = len(re.findall(r'<div\b', content))
closes = len(re.findall(r'</div>', content))
print('div opens: ' + str(opens))
print('div closes: ' + str(closes))
if opens == closes:
    print('Balance: OK')
else:
    print('Balance: MISMATCH, diff = ' + str(opens - closes))
