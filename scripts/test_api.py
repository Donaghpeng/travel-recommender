import urllib.request, json
r = urllib.request.urlopen('http://127.0.0.1:8000/api/recommend?budget=4000&days=5&date=2026-07&departure=%E4%B8%8A%E6%B5%B7&travelers=%E6%83%85%E4%BE%A3&region=%E5%9B%BD%E5%86%85&preferences=%E6%B5%B7%E6%BB%A9,%20%E7%BE%8E%E9%A3%9F')
data = json.loads(r.read())
print(f'Status: {r.status}')
cnt = len(data.get('results',[]))
print(f'Results: {cnt}')
if cnt:
    r0 = data['results'][0]
    print(f'Top: {r0["name_cn"]} ({r0["total_score"]})')
    print(f'Type: {r0.get("type")}')
    if r0.get('scores'):
        print(f'Scores: {r0["scores"]}')
