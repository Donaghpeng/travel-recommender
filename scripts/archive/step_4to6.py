import sys, os
sys.stdout.reconfigure(encoding='utf-8')

html_path = r'C:\Users\Donaghy\Desktop\travel-recommender\static\index.html'
js_path = r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js'

# ─── CSS CLEANUP ───
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Remove orphaned CSS blocks
remove_blocks = [
    ('/* ── Detail bar ── */', '/* ── Image ── */'),
]

for (start_marker, end_marker) in remove_blocks:
    s = html.find(start_marker)
    e = html.find(end_marker, s)
    if s >= 0 and e > s:
        html = html[:s] + html[e:]
        print(f'Removed: {start_marker[:30]}')

# Remove .good .ok .bad if standalone
for cls in ['.good{', '.ok{', '.bad{']:
    while cls in html:
        i = html.find(cls)
        # Find the closing }
        j = html.find('}', i) + 1
        html = html[:i] + html[j:]
        print(f'Removed: {cls}')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'index.html: {len(html)} bytes')

# ─── JS CHANGES ───
# Step 4: Add city type → color mapping + image placeholder in renderResults
# Step 5: Update sel-circle interactions
# Step 6: Update drawer styling
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Step 4: Add type → gradient mapping
if 'var typeGradients' not in js:
    map_code = '''
// ── 城市类型 → 渐变色映射 ──
var typeGradients = {
  "海滨": ["#0ea5e9","#06b6d4"],
  "海岛": ["#0ea5e9","#06b6d4"],
  "海滩": ["#0ea5e9","#06b6d4"],
  "古镇": ["#8b5cf6","#a78bfa"],
  "历史": ["#8b5cf6","#a78bfa"],
  "古城": ["#8b5cf6","#a78bfa"],
  "自然": ["#10b981","#34d399"],
  "风光": ["#10b981","#34d399"],
  "山水": ["#10b981","#34d399"],
  "城市": ["#6366f1","#a78bfa"],
  "都市": ["#6366f1","#a78bfa"],
};

function getTypeGradient(type) {
  if (!type) return ["#6366f1","#a78bfa"];
  for (var k in typeGradients) {
    if (type.indexOf(k) >= 0) return typeGradients[k];
  }
  return ["#a78bfa","#c4b5fd"];
}
'''
    # Insert after escapeHtml function
    idx = js.find('function escapeHtml')
    if idx >= 0:
        end = js.find('\n\n', idx)
        if end < 0: end = js.find('\n//', idx)
        if end < 0: end = idx + 200
        # Insert after escapeHtml
        efn_end = js.find('}', idx) + 1
        js = js[:efn_end+1] + map_code + js[efn_end+1:]
        print('Added typeGradients mapping')
    else:
        print('Could not find escapeHtml position')

# Step 4: Update renderResults to use new card structure
old_render_start = 'function renderResults(results) {'
old_render = js.find(old_render_start)
if old_render >= 0:
    new_render_func = '''function renderResults(results) {
  var html = '<div class="results-header"><h2>推荐目的地</h2><span class="results-divider"></span><span id="selLabel" style="font-size:12px;color:var(--accent);font-weight:500"></span></div>';
  html += '<div class="preview-grid">';
  var bc = ["#a78bfa", "#8b5cf6", "#7c3aed", "#6d28d9", "#5b21b6"];
  for (var i = 0; i < results.length; i++) {
    var r = results[i];
    var s = r.scores;
    var rankColor = bc[Math.min(i, 4)];
    var type = r.type || '';
    var grad = getTypeGradient(type);
    var cityChar = (r.name_cn || r.name).charAt(0);
    var warnings = r.weather_warnings || [];
    var warnBadge = '';
    if (warnings.length > 0) {
      warnBadge = '<span class="warn-badge warn-' + warnings[0].level + '">' + warnings[0].icon + ' ' + escapeHtml(warnings[0].short || '') + '</span>';
    }
    // 注意：sel-circle 的 onclick 调 toggleSel(i,this)，this 必须传 .sel-circle 元素
    html += '<div class="preview-card" style="animation-delay:' + (i * 0.06) + 's">';
    html += '<div class="preview-image" style="background:linear-gradient(135deg,' + grad[0] + ',' + grad[1] + ')">';
    html += '<span class="city-letter">' + escapeHtml(cityChar) + '</span>';
    html += '<span class="sel-circle" onclick="event.stopPropagation();toggleSel(' + i + ',this)"></span>';
    html += '</div>';
    html += '<div class="preview-body">';
    html += '<div class="preview-header"><span class="preview-rank">#' + (i + 1) + '</span>';
    html += '<span class="preview-name">' + escapeHtml(r.name_cn || r.name) + '</span>';
    html += '<span class="preview-score">' + r.total_score + '</span></div>';
    // 5-dimension score bars
    html += '<div class="preview-stats">';
    var dims = [
      {label:'\\u5929\\u6c14', key:'weather', val: s.weather},
      {label:'\\u6210\\u672c', key:'cost', val: s.cost},
      {label:'\\u8def\\u7ebf', key:'route', val: s.route},
      {label:'\\u8bc4\\u4ef7', key:'review', val: s.review},
      {label:'\\u504f\\u597d', key:'preference', val: s.preference}
    ];
    for (var di = 0; di < dims.length; di++) {
      var dv = dims[di].val;
      if (typeof dv !== 'number') dv = parseInt(dv) || 0;
      var pct = Math.round((dv / 5) * 100);
      var cls = 'c' + Math.round(dv);
      html += '<div class="preview-stat">';
      html += '<span class="stat-label">' + dims[di].label + '</span>';
      html += '<span class="stat-bar"><span class="stat-fill ' + cls + '" style="width:' + pct + '%"></span></span>';
      html += '<span class="stat-num">' + dv + '</span></div>';
    }
    html += '</div>';
    // Tags line
    html += '<div class="preview-tags">';
    html += '<span class="preview-tag">' + escapeHtml(type) + '</span>';
    html += warnBadge;
    html += '</div>';
    html += '<button class="preview-more" onclick="renderDrawer(' + i + ')"><span>\\u67e5\\u770b\\u8be6\\u60c5 </span><span class="arrow">\\u2192</span></button>';
    html += '</div></div>';
  }
  html += '</div>';
  document.getElementById("results").innerHTML = html;
  updateWeatherBadge();
}'''

    # Find the old renderResults
    fn_end = js.find('function renderDrawer', old_render)
    if fn_end < 0: fn_end = js.find('\n//', old_render + 50)
    if fn_end < 0: fn_end = old_render + 2000
    
    old_len = fn_end - old_render
    # More precise: find the exact closing of renderResults
    # Look for the last } of renderResults function
    depth = 0
    in_func = False
    end_pos = old_render
    for pos in range(old_render, min(old_render + 3000, len(js))):
        if js[pos] == '{':
            depth += 1
            in_func = True
        elif js[pos] == '}':
            depth -= 1
            if in_func and depth == 0:
                end_pos = pos + 1
                break
    
    js = js[:old_render] + new_render_func + '\n\n' + js[end_pos:]
    print(f'Replaced renderResults ({end_pos - old_render} -> {len(new_render_func)} chars)')
else:
    print('renderResults not found!')

# Step 6: Update renderDrawer styling (add editorial styling)
# Find the drawTitle and drawBody usage
if 'renderDrawer' in js:
    # Update drawer content to use editorial styling
    # The drawer content is built in renderDrawer function
    print('renderDrawer function found - will update styling via CSS (already done)')
else:
    print('WARNING: renderDrawer not found in JS')

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print(f'app.js: {len(js)} bytes')
