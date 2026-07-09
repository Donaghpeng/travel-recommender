import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact region around tab-poi, tab-multi, and tab-recommend closing
# tab-poi: "<div class=\"tab-content\" id=\"tab-poi\">"
poi_open_tag = '<div class="tab-content" id="tab-poi">'
poi_idx = content.find(poi_open_tag)
print('POI tab at:', poi_idx)

# tab-multi:
multi_open_tag = '<div class="tab-content" id="tab-multi">'
multi_idx = content.find(multi_open_tag)
print('Multi tab at:', multi_idx)

# Find tab-multi closing div - find the </div> after multi's content
# After multi open, there's card placeholder then <div id="multiResults"></div></div>
close_multi = content.find('</div>', multi_idx + 200)
print('First </div> after multi open at:', close_multi, repr(content[close_multi:close_multi+30]))

# Second </div> closes tab-multi
close_multi2 = content.find('</div>', close_multi + 10)
print('Second </div> at:', close_multi2, repr(content[close_multi2:close_multi2+30]))

# /tab-recommend
rec_close = content.find('<!-- /tab-recommend -->')
print('Recommend close at:', rec_close, repr(content[rec_close:rec_close+50]))

# Content from just before POI tab to just after recommend close
start = poi_idx - 50
end = rec_close + 60
print('\n=== Full snippet ===')
print(content[start:end])
