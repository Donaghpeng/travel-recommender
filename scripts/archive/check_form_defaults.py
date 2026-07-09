import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the search form section
start = content.find('search-form')
if start > 0:
    section = content[start:start+2000]
    print(section)
