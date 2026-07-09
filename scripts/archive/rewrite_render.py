import os, sys
sys.stdout.reconfigure(encoding='utf-8')
root = r'C:\Users\Donaghy\Desktop\travel-recommender\static'

with open(os.path.join(root, 'js', 'app.js'), 'r', encoding='utf-8') as f:
    content = f.read()

# Find renderResults function boundaries
start = content.find('function renderResults(results)')
fn_start = content.find('{', start)  # opening brace
fn_end = content.find('\n// ── Review Stars ──', start)

print(f"renderResults found at {start}, fn: {fn_start}, end: {fn_end}")

# Extract the function body (from opening { to end)
old_body = content[fn_start:fn_end]
print(f"Old body length: {len(old_body)}")
print(f"Starts with: {repr(old_body[:80])}")
print(f"Ends with: {repr(old_body[-80:])}")

new_body = '''{
  var html = '<div class="card" style="margin-bottom:16px"><h2 style="font-size:16px;color:var(--text-primary);margin-bottom:4px">推荐目的地 (' + results.length + ')</h2></div>';
  html += '<div class="preview-grid">';
  var bc = ["#ffd700", "#c0c0c0", "#cd7f32", "#667eea", "#667eea"];
  for (var i = 0; i < results.length; i++) {
    var r = results[i];
    var s = r.scores;
    var rankColor = bc[Math.min(i, 4)];
    var warnings = r.weather_warnings || [];
    var warnBadge = '';
    if (warnings.length > 0) {
      warnBadge = '<span class="warn-badge warn-' + warnings[0].level + '" style="font-size:10px;padding:1px 6px;margin-left:auto">' + warnings[0].icon + '</span>';
    }
    html += '<div class="preview-card" style="border-left-color:' + rankColor + '">';
    html += '<div class="preview-header"><span class="preview-rank" style="background:' + rankColor + '">#' + (i + 1) + '</span>';
    html += '<span class="preview-name">' + escapeHtml(r.name_cn || r.name) + '</span>';
    html += '<span class="preview-score">' + r.total_score + '</span></div>';
    // Stats grid
    html += '<div class="preview-stats">';
    html += '<span class="preview-stat"><span>天气</span><span class="' + sc(s.weather) + '">' + (r.weather_detail && r.weather_detail.temp_hi !== '-' ? r.weather_detail.temp_hi + '/' + r.weather_detail.temp_lo + '°C' : s.weather + '/5') + '</span></span>';
    html += '<span class="preview-stat"><span>成本</span><span class="' + sc(s.cost) + '">' + s.cost + '/5</span></span>';
    html += '<span class="preview-stat"><span>路线</span><span class="' + sc(s.route) + '">' + s.route + '/5</span></span>';
    html += '<span class="preview-stat"><span>评价</span><span class="' + sc(s.review) + '">' + s.review + '/5</span></span>';
    html += '<span class="preview-stat"><span>偏好</span><span class="' + sc(s.preference) + '">' + s.preference + '/5</span></span>';
    html += '</div>';
    // Type badge + weather warning
    html += '<div style="display:flex;align-items:center;gap:6px;margin-top:4px">';
    html += '<span style="font-size:11px;color:var(--text-muted);background:var(--bg-score);border-radius:4px;padding:1px 6px">' + escapeHtml(r.type || '') + '</span>';
    html += warnBadge;
    html += '</div>';
    html += '<button class="preview-more" onclick="renderDrawer(' + i + ')">查看详情 →</button>';
    html += '</div>';
  }
  html += '</div>';
  document.getElementById("results").innerHTML = html;
  updateWeatherBadge();
}

// ── 渲染详情抽屉 ──
function renderDrawer(idx) {
  var r = currentResults[idx];
  if (!r) return;
  var s = r.scores;
  var body = document.getElementById('drawerBody');
  var html = '';
  // AI 描述（精简）
  if (r.ai_blurb) {
    html += '<div class="ai-blurb" style="margin-bottom:16px"><span class="ai-tag">AI</span>' + escapeHtml(r.ai_blurb) + '</div>';
  }
  // 评分总览（进度条）
  html += '<h3 style="font-size:14px;margin:0 0 8px;color:var(--text-primary)">评分总览</h3>';
  html += '<div style="margin-bottom:16px">';
  var dims = [['成本', s.cost], ['路线', s.route], ['评价', s.review], ['天气', s.weather], ['偏好', s.preference]];
  for (var di = 0; di < dims.length; di++) {
    var val = dims[di][1];
    var lbl = dims[di][0];
    var pct = (val / 5) * 100;
    html += '<div style="margin:4px 0;font-size:12px"><div style="display:flex;justify-content:space-between;margin-bottom:2px"><span>' + lbl + '</span><span class="' + sc(val) + '">' + val + '/5</span></div>'
      + '<div style="height:6px;background:var(--bg-score);border-radius:3px;overflow:hidden"><div style="height:100%;width:' + pct + '%;background:var(--accent);border-radius:3px;transition:width .5s"></div></div></div>';
  }
  html += '</div>';
  // 评分解释（折叠）
  if (r.score_explanations) {
    html += '<details style="margin-bottom:12px"><summary style="font-size:13px;font-weight:600;color:var(--accent);cursor:pointer;padding:4px 0">评分详情 ▸</summary>';
    html += '<div style="padding:8px;background:var(--bg-explanation);border-radius:8px;margin-top:4px;font-size:12px;line-height:1.8">';
    var ex = r.score_explanations;
    html += '<div><b>成本</b> (' + s.cost + '/5) — ' + escapeHtml(ex.cost || '') + '</div>';
    html += '<div><b>路线</b> (' + s.route + '/5) — ' + escapeHtml(ex.route || '') + '</div>';
    html += '<div><b>评价</b> (' + s.review + '/5) — ' + escapeHtml(ex.review || '') + '</div>';
    html += '<div><b>偏好</b> (' + s.preference + '/5) — ' + escapeHtml(ex.preference || '') + '</div>';
    html += '</div></details>';
  }
  // 天气预警
  if (r.weather_warnings && r.weather_warnings.length > 0) {
    html += '<div class="warn-box" style="margin-bottom:12px">';
    for (var w = 0; w < r.weather_warnings.length; w++) {
      var ww = r.weather_warnings[w];
      html += '<span class="warn-badge warn-' + ww.level + '">' + ww.icon + ' ' + escapeHtml(ww.label) + '</span>';
    }
    html += '</div>';
  }
  // 费用预估（折叠）
  if (r.estimate_detail) {
    var ed = r.estimate_detail;
    html += '<details style="margin-bottom:12px"><summary style="font-size:13px;font-weight:600;color:var(--accent);cursor:pointer;padding:4px 0">费用预估 ▸</summary>';
    html += '<div class="detail-bar" style="margin-top:4px">';
    html += '<span>🏨 住宿 <b>¥' + ed.hotel + '</b></span>';
    html += '<span>🍜 餐饮 <b>¥' + ed.food + '</b></span>';
    html += '<span>🎫 门票 <b>¥' + ed.ticket + '</b></span>';
    html += '</div></details>';
  }
  // 行程（折叠）
  if (r.itinerary && r.itinerary.days) {
    html += '<details style="margin-bottom:12px"><summary style="font-size:13px;font-weight:600;color:var(--accent);cursor:pointer;padding:4px 0">行程 ' + r.itinerary.total_days + ' 天 ▸</summary>';
    html += '<div class="itin-box" style="margin-top:4px">';
    for (var di = 0; di < r.itinerary.days.length; di++) {
      var dd = r.itinerary.days[di];
      html += '<div class="itin-day"><b>第' + (di + 1) + '天</b> ' + escapeHtml(dd.morning) + '</div>';
    }
    html += '</div></details>';
  }
  // POI 推荐
  if (r.poi_summary && r.poi_summary.length > 0) {
    html += '<h3 style="font-size:14px;margin:16px 0 8px;color:var(--text-primary)">📍 热门景点</h3>';
    for (var pi = 0; pi < Math.min(5, r.poi_summary.length); pi++) {
      var p = r.poi_summary[pi];
      html += '<div style="padding:6px 0;border-bottom:1px solid var(--border-default);font-size:12px;display:flex;justify-content:space-between">';
      html += '<span>' + escapeHtml(p.name) + '</span>';
      html += '<span style="color:var(--text-muted)">' + (p.rating || '') + '</span></div>';
    }
  }
  // 联游方案链接
  html += '<div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-default)">';
  html += '<button class="mc-btn" onclick="showMultiCityCard();closeDrawer()" style="width:100%;text-align:center">🔄 查看联游方案</button>';
  html += '</div>';
  body.innerHTML = html;
  openDrawer(r.name_cn || r.name);
}'''

content = content[:fn_start] + new_body + content[fn_end:]
with open(os.path.join(root, 'js', 'app.js'), 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! Replacement successful.")
