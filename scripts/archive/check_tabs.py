import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'index.html'),'r',encoding='utf-8') as f:
    content = f.read()

poi_start = content.find('id="tab-poi"')
poi_end = content.find('div class="tab-content" id="tab-multi"', poi_start)
print('=== tab-poi content ===')
print(content[poi_start:poi_end+300])

print()
print()

multi_start = content.find('id="tab-multi"')
container_end = content.find('<!-- --- \u4fa7\u6ed1\u62bd\u5c49 --->')
print('=== tab-multi content ===')
print(content[multi_start:container_end])
