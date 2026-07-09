import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js','r',encoding='utf-8') as f: c=f.read()

# Find addBookingButtons function
i=c.find('function addBookingButtons')
j=c.find('\nfunction', i+10)
if j<0: j=i+2000
print(c[i:j])
print('===')
# Find calls to addBookingButtons 
cnt=0
pos=0
while True:
    pos=c.find('addBookingButtons', pos)
    if pos<0: break
    line_start=c.rfind('\n',0,pos)+1
    line_end=c.find('\n',pos)
    print(f'call at {pos}: {c[line_start:line_end]}')
    pos+=1
    cnt+=1
print(f'{cnt} calls total')
