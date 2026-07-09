import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

# ── Step 10: 对比分析降级 ──

js_path = r'C:\Users\Donaghy\Desktop\travel-recommender\static\js\app.js'
html_path = r'C:\Users\Donaghy\Desktop\travel-recommender\static\index.html'

# ── 1. app.js: Add sel-circle to renderResults and keep toggleSel, remove openCompare ──
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1a. Add sel-circle to preview card header (after rank, before name)
old = 'html += \'<div class="preview-header"><span class="preview-rank" style="background:\' + rankColor + \'">#\' + (i + 1) + \'</span>\';\n    html += \'<span class="preview-name">\' + escapeHtml(r.name_cn || r.name) + \'</span>\';'
new = 'html += \'<div class="preview-header"><span class="sel-circle" onclick="event.stopPropagation();toggleSel(\' + i + \',this)" style="width:20px;height:20px;font-size:11px"></span>\';\n    html += \'<span class="preview-rank" style="background:\' + rankColor + \'">#\' + (i + 1) + \'</span>\';\n    html += \'<span class="preview-name">\' + escapeHtml(r.name_cn || r.name) + \'</span>\';'

if old in js:
    js = js.replace(old, new, 1)
    print('1a. Added sel-circle to preview cards: OK')
else:
    print('1a. FAILED - pattern not found')

# 1b. Remove openCompare function body but keep the declaration as no-op
old2 = 'function openCompare() {\n  if (selectedIdx.length < 2) return;\n  var grid = document.getElementById("compareGrid");\n  grid.innerHTML = "";\n  for (var si = 0; si < selectedIdx.length; si++) {\n    var r = currentResults[selectedIdx[si]];\n    var s = r.scores || {};\n    var h = \'<div class="compare-col"><h3>\' + escapeHtml(r.name_cn || r.name) + \'</h3>\';\n    h += \'<div class="stat"><span class="lbl">总分</span><span class="val">\' + r.total_score + \'</span></div>\';\n    h += \'<div class="stat"><span class="lbl">天气</span><span class="val">\' + s.weather + \'/5</span></div>\';\n    h += \'<div class="stat"><span class="lbl">成本</span><span class="val">\' + s.cost + \'/5</span></div>\';\n    h += \'<div class="stat"><span class="lbl">路线</span><span class="val">\' + s.route + \'/5</span></div>\';\n    h += \'<div class="stat"><span class="lbl">评价</span><span class="val">\' + s.review + \'/5</span></div>\';\n    h += \'<div class="stat"><span class="lbl">偏好</span><span class="val">\' + s.preference + \'/5</span></div>\';\n    // Weather warnings\n    var ws = r.weather_warnings || [];\n    if (ws.length) {\n      h += \'<div class="stat"><span class="lbl">预警</span><span class="val" style="color:var(--red);font-size:12px">\';\n      for (var wi = 0; wi < ws.length; wi++) {\n        h += ws[wi].icon + \' \' + escapeHtml(ws[wi].short || \'\') + (wi < ws.length - 1 ? \' \' : \'\');\n      }\n      h += \'</span></div>\';\n    }\n    h += \'</div>\';\n    grid.innerHTML += h;\n  }\n  document.getElementById("compareModal").classList.add("active");\n}'

new2 = 'function openCompare() {\n  showToast("\u5df2\u6807\u8bb0 " + selectedIdx.length + " \u4e2a\u57ce\u5e02");\n}'

if old2 in js:
    js = js.replace(old2, new2, 1)
    print('1b. Replaced openCompare: OK')
else:
    print('1b. openCompare pattern not found, trying partial match...')
    # Try finding just the function header
    fi = js.find('function openCompare()')
    if fi >= 0:
        # Find closing brace
        depth = 0
        in_func = False
        end = fi
        for pos in range(fi, len(js)):
            if js[pos] == '{':
                depth += 1; in_func = True
            elif js[pos] == '}':
                depth -= 1
                if in_func and depth == 0:
                    end = pos + 1
                    break
        js = js[:fi] + 'function openCompare() {\n  showToast("\\u5df2\\u6807\\u8bb0 " + selectedIdx.length + " \\u4e2a\\u57ce\\u5e02");\n}\n' + js[end:]
        print('1b. Replaced openCompare (partial): OK')

# 1c. Update toggleSel to show selection count as text instead of button text
old3 = '  var btn = document.getElementById("cmpBtn");\n  if (btn) {\n    btn.disabled = selectedIdx.length < 2;\n    btn.textContent = "\\u5bf9\\u6bd4 (" + selectedIdx.length + ")";\n  }'
new3 = '  // \\u66f4\\u65b0\\u5df2\\u6807\\u8bb0\\u6570\\u91cf\n  var selLabel = document.getElementById("selLabel");\n  if (selLabel) {\n    selLabel.textContent = selectedIdx.length > 0 ? "\\u5df2\\u6807\\u8bb0 " + selectedIdx.length + " \\u4e2a\\u57ce\\u5e02" : "";\n  }'

if old3 in js:
    js = js.replace(old3, new3, 1)
    print('1c. Updated toggleSel text: OK')
else:
    print('1c. FAILED - toggleSel pattern not found')
    # Show what actually exists
    i = js.find('function toggleSel')
    if i >= 0:
        print('  toggleSel found, showing content:')
        print(js[i:i+500])

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print(f'\napp.js updated: {len(js)} bytes')

# ── 2. index.html: Remove compareModal HTML ──
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the compareModal div
old_modal = '<div class="modal-overlay" id="compareModal" onclick="this.classList.remove(\'active\')">\n<div class="modal" onclick="event.stopPropagation()">\n<span class="close" onclick="document.getElementById(\'compareModal\').classList.remove(\'active\')">&times;</span>\n<h2>\u76ee\u7684\u5730\u5bf9\u6bd4</h2>\n<div class="compare-grid" id="compareGrid"></div>\n</div>\n</div>'

if old_modal in html:
    html = html.replace(old_modal, '<!-- compareModal removed in Step 10 -->', 1)
    print('\n2. Removed compareModal HTML: OK')
else:
    print('\n2. FAILED - compareModal HTML not found')

# Remove compare modal CSS section
old_css_start = '/* \u2500\u2500 Compare Modal \u2500\u2500 */'
old_css_end = '/* \u2500\u2500 Review popup \u2500\u2500 */'

cs = html.find(old_css_start)
ce = html.find(old_css_end, cs)
if cs >= 0 and ce >= 0:
    html = html[:cs] + html[ce:]
    print('   Removed Compare Modal CSS: OK')
else:
    print('   Compare Modal CSS not found (maybe already removed)')

# Also remove compare-bar CSS if it references compare logic
# Keep .compare-bar as it's used elsewhere (maybe keep)

# Add selLabel element inside results container (before preview-grid)
sel_label = '<div id="selLabel" style="text-align:center;font-size:12px;color:var(--text-muted);margin-bottom:8px"></div>\n    '
old_results = '<div class="preview-grid">'
new_results = sel_label + '<div class="preview-grid">'
if old_results in html:
    html = html.replace(old_results, new_results, 1)
    print('   Added selLabel: OK')
else:
    print('   selLabel add FAILED')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'index.html updated: {len(html)} bytes')
