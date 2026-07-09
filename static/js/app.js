// app.js — 旅行推荐系统核心逻辑
// ── 全局状态 ──
var selectedIdx = [];
var currentResults = [];

// ── 颜色映射 ──
function sc(v) { return v >= 4 ? "good" : v >= 2.5 ? "ok" : "bad"; }

function bgGrad(type) {
  var g = {
    Beach: ["#0077b6", "#00b4d8"],
    Island: ["#0096c7", "#48cae4"],
    Mountain: ["#2d6a4f", "#52b788"],
    Nature: ["#1b4332", "#40916c"],
    City: ["#3a0ca3", "#4361ee"],
    Culture: ["#7209b7", "#b5179e"],
    AncientTown: ["#7f2d2d", "#c1121f"],
    Food: ["#e85d04", "#f48c06"],
    Adventure: ["#d00000", "#e63946"]
  };
  var c = g[type] || ["#667eea", "#764ba2"];
  return "linear-gradient(135deg," + c[0] + "," + c[1] + ")";
}

// ── 吐司通知 ──
function showToast(msg) {
  var el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(function() { el.style.display = "none"; }, 3000);
}

// ── Tab 状态管理 ──
var tabStates = {
  recommend: { searchParams: null, results: null, selectedIdx: [] },
  poi: { searchParams: null, results: null, page: 1 },
  multi: { results: null }
};
var currentTab = 'recommend';

// ── Tab 初始化 ──
function initTabs() {
  var btns = document.querySelectorAll('.tab-btn');
  btns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var tab = this.dataset.tab;
      switchTab(tab);
    });
  });
}

function switchTab(tab) {
  // Update nav buttons
  document.querySelectorAll('.tab-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.tab === tab);
  });
  // Update tab content visibility
  document.querySelectorAll('.tab-content').forEach(function(c) {
    c.classList.toggle('active', c.id === 'tab-' + tab);
  });
  currentTab = tab;
  // Auto-trigger multi-city when switching to that tab with search results
  if (tab === 'multi' && currentResults && currentResults.length > 0) {
    showMultiCityCard();
  }
}

// ── 侧滑抽屉 ──
function openDrawer(title) {
  document.getElementById('drawerOverlay').classList.add('active');
  setTimeout(function() {
    document.getElementById('drawer').classList.add('open');
  }, 10);
  document.getElementById('drawerTitle').textContent = title;
  document.body.style.overflow = 'hidden';
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  setTimeout(function() {
    document.getElementById('drawerOverlay').classList.remove('active');
    document.body.style.overflow = '';
  }, 350);
}

// ── 骨架卡片 ──
function skeletonCard() {
  return '<div class="skeleton-card"><div class="sk-img"></div><div class="sk-line"></div><div class="sk-line"></div><div class="sk-score"><div></div><div></div><div></div><div></div><div></div></div></div>';
}

// ── 搜索 ──
// ── 搜索 ──
document.getElementById('searchBtn')?.addEventListener('click', function() {
  var btn = document.getElementById("searchBtn");
  var resEl = document.getElementById("results");
  if (!btn || !resEl) return;

  btn.classList.add("loading");
  resEl.innerHTML = "";
  for (var i = 0; i < 3; i++) resEl.innerHTML += skeletonCard();

  var b = document.getElementById("budget").value;
  var d = document.getElementById("days").value;
  var td = document.getElementById("travel_date").value;
  var dp = document.getElementById("departure").value;
  var p = document.getElementById("preferences").value;
  var t = document.getElementById("travelers").value;
  var r = document.getElementById("region").value;

  var url = "/api/recommend?budget=" + encodeURIComponent(b)
    + "&days=" + encodeURIComponent(d)
    + "&travel_date=" + encodeURIComponent(td)
    + "&departure=" + encodeURIComponent(dp)
    + "&preferences=" + encodeURIComponent(p)
    + "&travelers=" + encodeURIComponent(t)
    + "&region=" + encodeURIComponent(r);

  var xhr = new XMLHttpRequest();
  xhr.open("GET", url, true);
  xhr.onload = function () {
    btn.classList.remove("loading");
    if (xhr.status !== 200) {
      resEl.innerHTML = "";
      showToast("\u670d\u52a1\u5668\u9519\u8bef: " + xhr.status);
      return;
    }
    var data;
    try {
      data = JSON.parse(xhr.responseText);
    } catch (e) {
      resEl.innerHTML = "";
      showToast("\u6570\u636e\u9519\u8bef: " + e.message);
      return;
    }
    currentResults = data.results || [];
    selectedIdx = [];
    if (currentResults.length === 0) {
      var w = document.getElementById("mapWrap");
      if (w) w.classList.remove("active");
      resEl.innerHTML = '<div class="card"><div class="empty-msg"><div class="ek">\u{1F3DD}</div>\u6ca1\u6709\u627e\u5230\u5339\u914d\u7684\u76ee\u7684\u5730<br>\u8bd5\u8bd5\u8c03\u6574\u9884\u7b97\u6216\u5929\u6570</div></div>';
      return;
    }
    renderResults(currentResults);
    if (typeof showOnMap === "function") {
      showOnMap(currentResults, dp);
    }
    postRender(currentResults, dp);
  };
  xhr.onerror = function () {
    btn.classList.remove("loading");
    resEl.innerHTML = "";
    showToast("\u7f51\u7edc\u8fde\u63a5\u5931\u8d25");
  };
  xhr.send();
});


// ── POI跳转到推荐Tab ──
function goToRecommendFromPOI(city) {
  if (!city) return;
  // 设置偏好框
  var pref = document.getElementById("preferences");
  if (pref) {
    var old = pref.value;
    if (old && old !== city) {
      pref.value = city + ", " + old;
    } else {
      pref.value = city;
    }
  }
  // 切换到推荐Tab
  switchTab("recommend");
  // 触发搜索
  var btn = document.getElementById("searchBtn");
  if (btn) btn.click();
}
// ── 渲染结果 ──
function renderResults(results) {
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
      {label:'\u5929\u6c14', key:'weather', val: s.weather},
      {label:'\u6210\u672c', key:'cost', val: s.cost},
      {label:'\u8def\u7ebf', key:'route', val: s.route},
      {label:'\u8bc4\u4ef7', key:'review', val: s.review},
      {label:'\u504f\u597d', key:'preference', val: s.preference}
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
    html += '<button class="preview-more" onclick="renderDrawer(' + i + ')"><span>\u67e5\u770b\u8be6\u60c5 </span><span class="arrow">\u2192</span></button>';
    html += '</div></div>';
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
  } else {
    html += '<div class="ai-blurb" style="margin-bottom:16px;background:var(--bg-surface);border-left-color:var(--text-muted)"><span class="ai-tag pending">AI</span><span style="color:var(--text-muted);font-style:italic">🤖 AI 描述生成中，刷新后可见...</span></div>';
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
}
// ── Review Stars ──
function renderStars(rating) {
  if (!rating || rating <= 0) return '';
  var full = Math.floor(rating);
  var half = (rating - full) >= 0.3 && (rating - full) < 0.8;
  var empty = 5 - full - (half ? 1 : 0);
  var s = '';
  for (var i = 0; i < full; i++) s += '\u2605';
  if (half) s += '\u00bd';
  for (var i = 0; i < empty; i++) s += '\u2606';
  return '<span style="color:#f59e0b;font-size:14px;letter-spacing:1px">' + s + '</span>';
}


// ── 辅助: HTML 转义 ──

// ── Post-render: add extra features via DOM (safer than template strings)
function postRender(results, dep) {
  setTimeout(function(){showTravelTips(results);}, 1000);
  loadDestImages(results);
  loadDestImages(results);
  addPriceTrends(results, dep);
  // Warnings are already in r.weather_warnings from the API response
}

// ── More menu toggle ──
function toggleMoreMenu(e){
  e.stopPropagation();
  var dd=document.getElementById("moreDropdown");
  if(dd)dd.classList.toggle("active");
}
function closeMoreMenu(){
  var dd=document.getElementById("moreDropdown");
  if(dd)dd.classList.remove("active");
}
document.addEventListener("click",function(e){
  var dd=document.getElementById("moreDropdown");
  var mb=document.querySelector(".more-btn");
  if(dd&&dd.classList.contains("active")&&!dd.contains(e.target)&&e.target!==mb){
    dd.classList.remove("active");
  }
});

function addBookingButtons(results) {
  for (var i = 0; i < results.length; i++) {
    var cards = document.querySelectorAll(".preview-card");
    if (!cards[i]) continue;
    var dest = (results[i].name_cn || results[i].name).split(" (")[0].split("/")[0];
    var wrap = document.createElement("div");
    wrap.style.cssText = "display:flex;gap:4px;margin-top:4px";
    var btn = document.createElement("a");
    btn.className = "book-btn";
    btn.textContent = "\u67e5\u4ef7\u683c";
    var bid = "bk_" + i;
    btn.id = bid;
    var pop = document.createElement("div");
    pop.className = "book-popup";
    pop.id = "bkp_" + i;
    wrap.appendChild(btn);
    wrap.appendChild(pop);
    cards[i].appendChild(wrap);
    // Wire click
    btn.onclick = function(d, b, p) {
      return function() { showBooking(d, b, p); };
    }(dest, bid, "bkp_" + i);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

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

// ── 选择/对比 ──
function toggleSel(idx, circle) {
  var i = selectedIdx.indexOf(idx);
  var card = circle.closest ? circle.closest(".preview-card") : circle.parentNode;
  if (i >= 0) {
    selectedIdx.splice(i, 1);
    circle.classList.remove("on");
    card.classList.remove("selected");
  } else if (selectedIdx.length < 3) {
    selectedIdx.push(idx);
    circle.classList.add("on");
    card.classList.add("selected");
  }
  // \u66f4\u65b0\u5df2\u6807\u8bb0\u6570\u91cf
  var selLabel = document.getElementById("selLabel");
  if (selLabel) {
    selLabel.textContent = selectedIdx.length > 0 ? "\u5df2\u6807\u8bb0 " + selectedIdx.length + " \u4e2a\u57ce\u5e02" : "";
  }
}

function openCompare() {
  showToast("\u5df2\u6807\u8bb0 " + selectedIdx.length + " \u4e2a\u57ce\u5e02");
}



// ── Price Trend ──
function trendArrow(t){
  if(t==="rising") return "↑";
  if(t==="falling") return "↓";
  return "→";
}
function trendColor(t){
  if(t==="rising") return "#ef4444";
  if(t==="falling") return "#10b981";
  return "#999";
}
function fetchTrend(dep,dest,elId){
  var u="/api/flight/trend?departure="+encodeURIComponent(dep)+"&destination="+encodeURIComponent(dest)+"&days=30";
  var x=new XMLHttpRequest();
  x.open("GET",u,true);
  x.onload=function(){
    if(x.status!==200)return;
    try{showTrend(JSON.parse(x.responseText),elId)}catch(e){}
  };
  x.send();
}
function showTrend(data,elId){
  var el=document.getElementById(elId);
  if(!el)return;
  var his=data.history||[];
  if(his.length<2){
    el.innerHTML='<span style="font-size:11px;color:#999">当前 ¥'+data.current_price+' (范围 ¥'+data.price_range.low+'-'+data.price_range.high+')</span>';
    return;
  }
  var w=260,h=80,pt=8,pr=8,pb=18,pl=35,cw=w-pl-pr,ch=h-pt-pb;
  var vals=his.map(function(hh){return hh.price;});
  var mn=Math.min.apply(null,vals),mx=Math.max.apply(null,vals),rg=mx-mn||1;
  var pts=his.map(function(hh,i){
    var x=pl+(i/(his.length-1))*cw;
    var y=pt+ch-((hh.price-mn)/rg)*ch;
    return x+","+y;
  });
  var poly=pts.join(" "),col=trendColor(data.trend),arr=trendArrow(data.trend);
  var s='<svg width="'+w+'" height="'+h+'" xmlns="http://www.w3.org/2000/svg">';
  s+='<rect width="'+w+'" height="'+h+'" fill="#fafafa" rx="6"/>';
  for(var gi=0;gi<=3;gi++){
    var gy=pt+(gi/3)*ch;
    var lbl=Math.round(mn+(1-gi/3)*rg);
    s+='<line x1="'+pl+'" y1="'+gy+'" x2="'+(w-pr)+'" y2="'+gy+'" stroke="#eee" stroke-width="1"/>';
    s+='<text x="'+(pl-3)+'" y="'+(gy+3)+'" text-anchor="end" font-size="9" fill="#999">¥'+lbl+'</text>';
  }
  s+='<polygon points="'+pl+','+(pt+ch)+' '+poly+' '+(w-pr)+','+(pt+ch)+'" fill="'+col+'22"/>';
  s+='<polyline points="'+poly+'" fill="none" stroke="'+col+'" stroke-width="2" stroke-linejoin="round"/>';
  var last=his[his.length-1],lx=pl+cw,ly=pt+ch-((last.price-mn)/rg)*ch;
  s+='<circle cx="'+lx+'" cy="'+ly+'" r="3" fill="'+col+'"/>';
  var tt=data.trend==="rising"?"上涨":data.trend==="falling"?"下降":"稳定";
  s+='<text x="'+(pl+5)+'" y="'+(pt+12)+'" font-size="10" fill="'+col+'" font-weight="bold">'+arr+' '+tt+' ¥'+data.current_price+'</text></svg>';
  el.innerHTML=s;
  el.style.display="block";
}
function addPriceTrends(rs,dep){
  for(var i=0;i<rs.length;i++){
    var dest=rs[i].name.split(" (")[0].split("/")[0];
    var id="pt_"+i;
    var cards=document.querySelectorAll(".preview-card");
    if(cards[i]){
      var wrap=document.createElement("div");
      wrap.className="pt-row";
      // Flight estimate
      if(rs[i].estimate_detail&&rs[i].estimate_detail.flight){
        var fSpan=document.createElement("span");
        fSpan.className="pt-flight";
        fSpan.innerHTML="✈ ¥<b>"+rs[i].estimate_detail.flight+"</b>";
        wrap.appendChild(fSpan);
      }
      // Trend SVG container
      var trendDiv=document.createElement("div");
      trendDiv.id=id;
      wrap.appendChild(trendDiv);
      // Booking icon button
      var bkBtn=document.createElement("a");
      bkBtn.className="book-btn-icon";
      bkBtn.textContent="[Price]";
      bkBtn.title="查价格";
      bkBtn.id="bk_"+i;
      wrap.appendChild(bkBtn);
      var pop=document.createElement("div");
      pop.className="book-popup";
      pop.id="bkp_"+i;
      wrap.appendChild(pop);
      bkBtn.onclick=(function(d,b,p){
        return function(e){e.stopPropagation();showBooking(d,b,p);};
      })(dest,"bk_"+i,"bkp_"+i);
      cards[i].appendChild(wrap);
      fetchTrend(dep,dest,id);
    }
  }
}


// ── Booking ──

function showBooking(dest,btnId,popupId){
  closeAllPops();
  var btn=document.getElementById(btnId),pop=document.getElementById(popupId);
  if(!btn||!pop)return;
  var dep=document.getElementById("departure").value;
  var date=document.getElementById("travel_date").value;
  var rect=btn.getBoundingClientRect();
  pop.style.position="fixed";
  pop.style.top=(rect.bottom+6)+"px";
  pop.style.left=Math.max(10,Math.min(rect.left,document.documentElement.clientWidth-270))+"px";
  pop.style.zIndex=9999;
  pop.innerHTML='<div style="text-align:center;padding:12px;color:#999;font-size:12px">\u52a0\u8f7d\u4e2d...</div>';
  pop.classList.add("active");
  var x=new XMLHttpRequest();
  x.open("GET","/api/booking?departure="+encodeURIComponent(dep)+"&destination="+encodeURIComponent(dest)+"&travel_date="+encodeURIComponent(date),true);
  x.onload=function(){
    if(x.status!==200){pop.innerHTML='<div style="font-size:12px;color:#999;text-align:center;padding:10px">\u6682\u65e0\u94fe\u63a5</div>';return}
    try{
      var d=JSON.parse(x.responseText);
      var h='<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border-bottom:1px solid #eee"><span style="font-weight:600;font-size:13px">\u9884\u8ba2\u94fe\u63a5</span><span style="cursor:pointer;color:#999;font-size:18px;line-height:1" onclick="closeAllPops()">&times;</span></div>';
      for(var pi=0;pi<d.platforms.length;pi++){
        var pf=d.platforms[pi];
        h+='<div style="font-size:11px;font-weight:600;color:'+pf.color+';padding:6px 10px 2px">'+pf.name+'</div>';
        for(var li=0;li<pf.links.length;li++){
          h+='<a href="'+pf.links[li].url+'" target="_blank" rel="noopener" style="display:block;padding:5px 10px;font-size:12px;text-decoration:none;color:#555;border-radius:4px;transition:background .1s" onmouseover="this.style.background=\"#f3f4f6\"" onmouseout="this.style.background=\"\""><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+pf.color+';margin-right:6px"></span>'+pf.links[li].label+'</a>';
        }
      }
      pop.innerHTML=h;
    }catch(e){pop.innerHTML='<div style="font-size:12px;color:#999;text-align:center;padding:10px">\u52a0\u8f7d\u5931\u8d25</div>'}
  };
  x.onerror=function(){pop.innerHTML='<div style="font-size:12px;color:#999;text-align:center;padding:10px">\u7f51\u7edc\u9519\u8bef</div>'};
  x.send();
}

function closeAllPops(){
  var pops=document.querySelectorAll(".book-popup.active");
  for(var pi=0;pi<pops.length;pi++)pops[pi].classList.remove("active");
}

document.addEventListener("click",function(e){
  var pops=document.querySelectorAll(".book-popup.active");
  if(pops.length===0)return;
  for(var pi=0;pi<pops.length;pi++){
    if(!pops[pi].contains(e.target)&&!e.target.closest(".booking-wrap")&&!e.target.classList.contains("book-btn")){
      pops[pi].classList.remove("active");return;
    }
  }
});


/* PDF export removed */




function loadDestImages(rs){
  if(!rs||!rs.length)return;
  for(var i=0;i<rs.length;i++){
    var el=document.getElementById("dimg_"+i);
    if(!el)continue;
    (function(idx,imgEl){
      var x=new XMLHttpRequest();
      x.open("GET","/api/dest-image?name="+encodeURIComponent(rs[idx].name)+"&name_cn="+encodeURIComponent(rs[idx].name_cn||"")+"&dest_type="+encodeURIComponent(rs[idx].type||""),true);
      x.onload=function(){
        if(x.status!==200)return;
        try{
          var d=JSON.parse(x.responseText);
          if(d.url){imgEl.onerror=function(){imgEl.style.display="none"};imgEl.src=d.url;imgEl.style.display="block"}
        }catch(e){}
      };
      x.send();
    })(i,el);
  }
}

function showTravelTips(rs) {
  for (var i = 0; i < rs.length; i++) {
    var r = rs[i];
    if (!r.hotel_advice && !r.sight_advice) continue;
    var cards = document.querySelectorAll(".preview-card");
    if (!cards[i]) continue;
    var tipDiv = document.createElement("div");
    tipDiv.style.cssText = "margin:6px 0 4px;font-size:11px;line-height:1.5";
    var tips = [];
    if (r.hotel_advice) {
      tips.push("<span style='background:#e0e7ff;padding:2px 6px;border-radius:4px;margin-right:4px'>" + r.hotel_advice.icon + "</span>" + r.hotel_advice.advice);
    }
    if (r.sight_advice) {
      tips.push('<span style="color:#888">' + r.sight_advice.advice + '</span>');
    }
    if (r.flight_advice && r.flight_advice.length > 0) {
      tips.push('<span style="color:#888">' + r.flight_advice[0].tip + '</span>');
    }
    tipDiv.innerHTML = '\u2714\ufe0f ' + tips.join(' | ');
    cards[i].appendChild(tipDiv);
  }
}




// ── Multi-City Routes ──
var _mcRoutes = [];


function showMultiCityCard(){
  var d=document;
  var multiRes=d.getElementById("multiResults");
  var placeholder=d.querySelector("#tab-multi > .card");
  if(!multiRes)return;

  // Hide placeholder, show loading
  if(placeholder)placeholder.style.display="none";
  multiRes.innerHTML='<div class="card"><h3>\u8054\u6e38\u65b9\u6848</h3><div style="text-align:center;padding:20px;color:var(--text-muted)">\u23f3 \u6b63\u5728\u751f\u6210\u8054\u6e38\u65b9\u6848...</div></div>';

  var b=d.getElementById("budget").value;
  var ds=d.getElementById("days").value;
  var dp=d.getElementById("departure").value;
  var p=d.getElementById("preferences").value;
  var t=d.getElementById("travelers").value;

  var x=new XMLHttpRequest();
  x.open("GET","/api/multi-city?budget="+encodeURIComponent(b)+"&days="+encodeURIComponent(ds)+"&departure="+encodeURIComponent(dp)+"&preferences="+encodeURIComponent(p)+"&travelers="+encodeURIComponent(t),true);
  x.onload=function(){
    if(x.status!=200){multiRes.innerHTML=mcEmpty();return}
    try{
      var dt=JSON.parse(x.responseText),rs=dt.routes||[];
      if(!rs.length){multiRes.innerHTML=mcEmpty();return}
      var h='<div style="margin-bottom:12px"><h3 style="font-size:18px;font-weight:700;margin:0 0 4px;color:var(--text-primary)">\u8054\u6e38\u65b9\u6848</h3><span style="font-size:12px;color:var(--text-muted,#999)">\u591a\u57ce\u5e02\u7ec4\u5408\u63a8\u8350</span></div>';
      for(var ri=0;ri<rs.length;ri++)h+=mcRenderCard(rs[ri],ri,dt.input||{});
      multiRes.innerHTML=h;
      setTimeout(mcLoadCityImgs,200);
    }catch(e){multiRes.innerHTML=mcEmpty()}
  };
  x.onerror=function(){multiRes.innerHTML=mcEmpty()};
  x.send();
}

function mcEmpty(){
  return '<div class="card"><h3>\u8054\u6e38\u65b9\u6848</h3><div style="text-align:center;padding:20px;color:var(--text-muted,#999);font-size:14px">\u6682\u65e0\u5339\u914d\u7684\u8054\u6e38\u65b9\u6848</div></div>';
}

function mcRenderCard(rt,ri,inp){
  var h='<div style="border:1px solid var(--border-card,#e2e8f0);border-radius:12px;padding:16px;margin:10px 0;background:var(--bg-card-alt,#fafbff)">';

  // Header
  h+='<div style="display:flex;justify-content:space-between;align-items:center"><h3 style="margin:0;font-size:15px">'+rt.icon+' '+rt.cluster_name+'</h3><span style="background:#ffd700;padding:2px 10px;border-radius:10px;font-weight:700;font-size:13px">'+rt.score+'</span></div>';
  h+='<div style="font-size:11px;color:var(--text-muted,#999);margin:4px 0 10px">'+rt.theme+'</div>';

  // ── Step 1: SVG Route Map ──
  h+=mcSVGRoute(rt);

  // ── Step 3: City Image Cards ──
  h+='<div style="display:flex;gap:8px;margin:10px 0;overflow-x:auto;padding-bottom:4px">';
  for(var ci=0;ci<rt.route.length;ci++){
    h+=mcCityImgCard(rt,ri,ci);
  }
  h+='</div>';

  // Budget bar
  h+=mcBudgetBar(rt,inp.budget||0);
  // Risk check section
  if (rt.risk) {
    h+=mcRiskSection(rt);
  }



  // ── Step 2: Daily Itinerary (collapsible) ──
  h+='<div style="margin:8px 0 0;border-top:1px solid var(--border-card,#e2e8f0);padding-top:8px">';
  h+='<div class="mc-itin-toggle" onclick="mcToggleItin('+ri+')" style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;color:var(--accent,#667eea);user-select:none">'
    +'<span style="font-size:10px;transition:transform .2s;display:inline-block" id="mcArr_'+ri+'">\u25b6</span>'
    +'\u67e5\u770b\u6bcf\u65e5\u884c\u7a0b</div>';
  h+='<div id="mcItin_'+ri+'" style="display:none;margin-top:6px">'+mcItinerary(rt)+'</div>';
  h+='</div>';

  h+='</div>';
  return h;
}

// ── Step 1: SVG Route ──
function mcSVGRoute(rt){
  var cs=rt.route,tds=rt.transport_details||[];
  if(cs.length<2) return '';
  var sw=600,sh=80,step=Math.min(180,Math.floor((sw-60)/Math.max(cs.length-1,1))),sx=40;
  var svg='<svg width="'+sw+'" height="'+sh+'" viewBox="0 0 '+sw+' '+sh+'" style="width:100%;height:auto;display:block">';
  svg+='<rect width="'+sw+'" height="'+sh+'" fill="transparent" rx="8"/>';

  var icons={'\u4e0a\u6d77':'\u{1F3D9}','\u676d\u5dde':'\u{1F3DB}','\u82cf\u5dde':'\u{1F3D8}','\u5357\u4eac':'\u{1F3DB}','\u4e4c\u9547':'\u{1F3F0}','\u6210\u90fd':'\u{1F334}','\u91cd\u5e86':'\u{1F5FC}','\u4e50\u5c71':'\u{1F5FB}','\u4e09\u4e9a':'\u{1F3D6}','\u6d77\u53e3':'\u{1F334}','\u4e07\u5b81':'\u{1F30A}','\u5927\u7406':'\u{1F3F0}','\u4e3d\u6c5f':'\u{1F5FB}','\u6606\u660e':'\u{1F33F}','\u6842\u6797':'\u{1F5FB}','\u9633\u6714':'\u{1F305}','\u5e7f\u5dde':'\u{1F3D9}','\u5317\u4eac':'\u{1F3DB}','\u5929\u6d25':'\u{1F3D9}','\u627f\u5fb7':'\u{1F3DB}'};

  for(var ci=0;ci<cs.length;ci++){
    var cx=sx+ci*step;
    var ic=icons[cs[ci]]||'\u25cf';
    svg+='<circle cx="'+cx+'" cy="40" r="14" fill="#667eea" opacity=".15"/>';
    svg+='<circle cx="'+cx+'" cy="40" r="10" fill="#667eea"/>';
    svg+='<text x="'+cx+'" y="45" text-anchor="middle" font-size="12" fill="#fff">'+ic+'</text>';
    svg+='<text x="'+cx+'" y="68" text-anchor="middle" font-size="11" fill="var(--text-secondary,#555)" font-weight="600">'+cs[ci]+'</text>';
    svg+='<text x="'+cx+'" y="18" text-anchor="middle" font-size="10" fill="var(--text-muted,#999)">'+rt.day_allocation[ci]+'\u5929</text>';

    if(ci<cs.length-1){
      var nx=sx+(ci+1)*step;
      svg+='<line x1="'+(cx+10)+'" y1="40" x2="'+(nx-10)+'" y2="40" stroke="#667eea" stroke-width="2" stroke-dasharray="4,3" opacity=".5"/>';
      svg+='<polygon points="'+(nx-16)+',35 '+(nx-16)+',45 '+(nx-10)+',40" fill="#667eea" opacity=".5"/>';
      var td=tds[ci];
      if(td){
        svg+='<text x="'+((cx+nx)/2)+'" y="30" text-anchor="middle" font-size="9" fill="var(--text-muted,#999)">'+td.mode+'</text>';
        svg+='<text x="'+((cx+nx)/2)+'" y="56" text-anchor="middle" font-size="9" fill="var(--text-muted,#999)">\u00a5'+td.cost+'</text>';
      }
    }
  }
  svg+='</svg>';
  return svg;
}

// ── Step 3: City Image Card ──
function mcCityImgCard(rt,ri,ci){
  var city=rt.route[ci],days=rt.day_allocation[ci]||1,bgt=rt.city_budgets[ci]||0;
  var imgId='mcimg_'+ri+'_'+ci;
  var cityId='mccity_'+ri+'_'+ci;
  return '<div style="flex:1;min-width:130px;border-radius:8px;overflow:hidden;border:1px solid var(--border-card,#e2e8f0);background:var(--bg-card,#fff);box-shadow:0 1px 3px rgba(0,0,0,.05)">'
    +'<div style="height:80px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden">'
    +'<span style="font-size:32px;opacity:.6">\u{1F3DD}</span>'
    +'<img id="'+imgId+'" city="'+city+'" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;display:none" onerror="this.style.display=\'none\'">'
    +'</div>'
    +'<div style="padding:8px"><div id="'+cityId+'" class="mc-city-name" style="font-size:13px;font-weight:600;color:var(--text-primary,#333)">'+city+'</div>'
    +'<div style="font-size:11px;color:var(--text-muted,#999);margin-top:4px">'+days+'\u5929</div>'
    +'<div style="font-size:13px;font-weight:700;color:var(--text-primary,#333);margin-top:2px">\u00a5'+bgt.toLocaleString()+'</div></div></div>';
}

function mcLoadCityImgs(){
  var imgs=document.querySelectorAll("img[id^='mcimg_']");
  imgs.forEach(function(el){
    var city=el.getAttribute("city");
    if(!city) return;
    // Try multiple endpoints for better image coverage
    var loadUrl=function(url){
      var x=new XMLHttpRequest();
      x.open("GET",url,true);
      x.onload=function(){
        if(x.status!=200) return;
        try{
          var d=JSON.parse(x.responseText);
          if(d&&d.url){el.src=d.url;el.style.display="block"}
        }catch(e){}
      };
      x.send();
    };
    loadUrl("/api/dest-image?name_cn="+encodeURIComponent(city)+"&dest_type=City");
  });
}

function mcBudgetBar(rt,total){
  var used=rt.total_budget_used||0;
  var pct=Math.min(100,Math.round(used/Math.max(total,1)*100));
  var col=pct>95?"#ef4444":pct>80?"#f59e0b":"#10b981";

  var h='<div style="margin:8px 0">';
  h+='<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted,#999);margin-bottom:3px">';
  h+='<span>\u00a5'+used.toLocaleString()+' / \u00a5'+total.toLocaleString()+'</span>';
  h+='<span style="color:'+col+';font-weight:600;font-size:12px">'+pct+'%</span></div>';

  h+='<div style="height:6px;border-radius:3px;background:var(--bg-score,#f3f4f6);overflow:hidden">';
  h+='<div style="height:100%;width:'+pct+'%;background:'+col+';border-radius:3px;transition:width .5s"></div></div>';

  // City bars
  if(rt.city_budgets&&rt.route){
    h+='<div style="display:flex;gap:4px;margin-top:5px">';
    for(var ci=0;ci<rt.route.length;ci++){
      var cp=Math.round(rt.city_budgets[ci]/Math.max(used,1)*100);
      h+='<div style="flex:'+cp+';font-size:9px;color:var(--text-muted,#999);text-align:center;padding:3px 2px;background:var(--bg-score,#f3f4f6);border-radius:3px">'+rt.route[ci]+' '+cp+'%</div>';
    }
    h+='</div>';
  }
  h+='</div>';
  return h;
}

// ── Risk Check Section ──


// -- Risk Check Section (v2) --
function mcRiskSection(rt) {
  var risk=rt.risk;
  var ov=risk.overall||"safe";
  var col={safe:"#10b981",caution:"#f59e0b",warning:"#ef4444",danger:"#dc2626"};
  var bg={safe:"#ecfdf5",caution:"#fffbeb",warning:"#fef2f2",danger:"#fef2f2"};
  var c=col[ov]||"#999";
  var b=bg[ov]||"#f3f4f6";
  var segs=risk.segments||[];
  var lm=risk.last_mile;

  var h='<div style="margin:8px 0 0;border-top:1px solid var(--border-card,#e2e8f0);padding-top:8px">';
  // Toggle header
  h+='<div class="mc-risk-toggle" onclick="mcToggleRisk(\''+rt.cluster_id.replace(/-/g,'_')+'\')" style="display:flex;align-items:center;gap:4px;cursor:pointer;font-size:12px;color:var(--text-secondary,#555);user-select:none">'
    +'<span style="display:inline-flex;justify-content:center;align-items:center;width:18px;height:18px;border-radius:9px;background:'+c+';color:#fff;font-size:10px;font-weight:700;line-height:18px;text-align:center" id="mcRiskIcon_'+rt.cluster_id.replace(/-/g,'_')+'">!</span>'
    +'<span style="font-weight:500;font-size:12px">\u4ea4\u901a\u8bc4\u4f30</span>'
    +'<span style="font-size:10px;background:'+b+';color:'+c+';padding:1px 7px;border-radius:4px;font-weight:600">'+risk.overall_label+'</span>'
    +'<span style="font-size:10px;color:var(--text-muted,#999);flex:1;padding-left:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+risk.summary+'</span>'
    +'<span style="font-size:10px;transition:transform .2s;display:inline-block;flex-shrink:0" id="mcRiskArr_'+rt.cluster_id.replace(/-/g,'_')+'">\u25b6</span>'
    +'</div>';

  h+='<div id="mcRisk_'+rt.cluster_id.replace(/-/g,'_')+'" style="display:block;margin-top:6px;font-size:12px">';

  // Segment details
  for (var si=0; si<segs.length; si++) {
    var s=segs[si];
    var sc=col[s.level]||"#999";
    var sb=bg[s.level]||"#f3f4f6";
    h+='<div style="padding:5px 8px;margin:3px 0;background:var(--bg-score,#f6f8fa);border-radius:6px;border:1px solid var(--border-card,#e2e8f0);font-size:11px">';
    // Route header
    h+='<div style="display:flex;align-items:center;gap:4px;margin-bottom:3px">';
    h+='<span style="font-weight:600;font-size:11px;color:var(--text-primary,#333)">'+s.from+'</span>';
    h+='<span style="color:#999;font-size:9px">\u279c</span>';
    h+='<span style="font-weight:600;font-size:11px;color:var(--text-primary,#333)">'+s.to+'</span>';
    h+='<span style="margin-left:auto;font-size:9px;color:#999;padding:0 4px;background:var(--bg-alt,#f0f0f0);border-radius:3px">'+s.mode+'</span>';
    h+='</div>';
    // Duration + arrival
    h+='<div style="display:flex;gap:6px;align-items:center">';
    h+='<span style="font-size:10px;color:#888">\u23f1'+s.duration_display+'</span>';
    h+='<span style="font-size:10px;color:#888">\xa0\xa0'+s.departure+' \u2192 '+s.arrival+'</span>';
    h+='<span style="margin-left:auto;font-size:10px;background:'+sb+';color:'+sc+';padding:1px 6px;border-radius:3px;font-weight:600">'+s.arrival_label+'</span>';
    h+='</div>';
    // Advice
    if (s.advice) {
      h+='<div style="font-size:10px;color:'+sc+';margin-top:3px">\u2139 '+s.advice+'</div>';
    }
    // Assessment basis tags — embedded in advice line for visibility
    var _eval_parts=[];
    if(s.transport_tip) _eval_parts.push(s.transport_tip);
    if(s.day_note) _eval_parts.push(s.day_note);
    if(_eval_parts.length){
      h+='<div style="font-size:11px;color:#555;margin-top:3px;padding:3px 6px;background:#f0f4ff;border-radius:4px;border:1px solid #d0d8f0;display:flex;gap:6px;flex-wrap:wrap">';
      for(var _ti=0;_ti<_eval_parts.length;_ti++){
        h+='<span style="background:#e0e8ff;padding:1px 8px;border-radius:3px;font-size:10px;color:#446">\ud83d\udcca '+_eval_parts[_ti]+'</span>';
      }
      h+='</div>';
    }
    h+='</div>';
  }

  // Last-mile
  if (lm) {
    var lc=col[lm.level]||"#999";
    var lb=bg[lm.level]||"#f3f4f6";
    h+='<div style="padding:5px 8px;margin:3px 0;background:var(--bg-score,#f6f8fa);border-radius:6px;border:1px solid var(--border-card,#e2e8f0);font-size:11px">';
    h+='<div style="display:flex;align-items:center;gap:4px;margin-bottom:3px">';
    h+='<span style="font-weight:600;font-size:11px;color:var(--text-primary,#333)">'+lm.city+'\u5230\u8fbe\uff0c\u6df1\u591c\u4ea4\u901a</span>';
    h+='<span style="margin-left:auto;font-size:10px;background:'+lb+';color:'+lc+';padding:1px 6px;border-radius:3px;font-weight:600">'+lm.label+'</span>';
    h+='</div>';
    if (lm.advice) {
      h+='<div style="font-size:10px;color:#555;margin:2px 0">\u2139 '+lm.advice+'</div>';
    }
    if (lm.suggest) {
      h+='<div style="font-size:10px;color:'+lc+';">\u2728 '+lm.suggest+'</div>';
    }
    h+='</div>';
  }

  h+='</div></div>';
  return h;
}

function mcToggleRisk(id) {
  var el=document.getElementById("mcRisk_"+id);
  var arr=document.getElementById("mcRiskArr_"+id);
  if(!el) return;
  if(el.style.display==="none"||el.style.display===""){
    el.style.display="block";
    if(arr) arr.style.transform="rotate(90deg)";
  }else{
    el.style.display="none";
    if(arr) arr.style.transform="rotate(0deg)";
  }
}



function mcToggleRisk(id) {
  var el=document.getElementById("mcRisk_"+id);
  var arr=document.getElementById("mcRiskArr_"+id);
  if(!el) return;
  if(el.style.display==="none"||el.style.display===""){
    el.style.display="block";
    if(arr) arr.style.transform="rotate(90deg)";
  }else{
    el.style.display="none";
    if(arr) arr.style.transform="rotate(0deg)";
  }
}



// ── Step 2: Daily Itinerary ──
function mcItinerary(rt){
  var actsByTheme={
    "water":["参观主要景点","品尝当地美食","古城漂泊","游览博物馆","民俗体验"],
    "food":["环境小吃早餐","主要景点游览","美食探店午餐","自由活动","夜市尝美食"],
    "beach":["海滩休闲","水上活动","日落散步","小岛出海","冷饮得美食"],
    "mountain":["登山","风景观台","野餐休息","山间清泉","归程休整"],
    "city":["主要景点","商圈购物","品尝特色美食","文化体验","夜景观赏"],
    "heritage":["历史遗迹","古城游览","博物馆","园林正式","特色民宿"],
    "default":["上午游览主要景点","中午尝当地美食","下午自由活动","晚间休憩","特色体验"]
  };
  var theme=rt.theme||"";
  var acts=actsByTheme.default;
  if(theme.indexOf("水")>=0||theme.indexOf("乡")>=0) acts=actsByTheme.water;
  else if(theme.indexOf("美食")>=0||theme.indexOf("饮")>=0) acts=actsByTheme.food;
  else if(theme.indexOf("海")>=0||theme.indexOf("度假")>=0) acts=actsByTheme.beach;
  else if(theme.indexOf("山")>=0||theme.indexOf("雪")>=0) acts=actsByTheme.mountain;
  else if(theme.indexOf("古都")>=0||theme.indexOf("文")>=0) acts=actsByTheme.heritage;
  else if(theme.indexOf("城市")>=0) acts=actsByTheme.city;

  var h='<div style="font-size:12px">';
  var dayNum=1;
  for(var ci=0;ci<rt.route.length;ci++){
    var city=rt.route[ci];
    var days=rt.day_allocation[ci]||1;
    for(var di=0;di<days;di++){
      var a1=acts[(di*2)%acts.length];
      var a2=acts[(di*2+1)%acts.length];
      var a3=acts[(di*2+2)%acts.length];
      var color=["#667eea","#f59e0b","#10b981"][dayNum%3];
      h+='<div style="padding:7px 10px;margin:4px 0;background:var(--bg-score,#f3f4f6);border-radius:8px;border-left:3px solid '+color+'">';
      h+='<div style="font-weight:600;font-size:12px;color:var(--text-primary,#333);margin-bottom:4px">\u7b2c'+dayNum+'天 (周'+"一二三四五六日"[dayNum%7]+') '+city+'</div>';
      h+='<div style="display:flex;gap:8px;align-items:flex-start;font-size:11px;color:var(--text-secondary,#555)">';
      h+='<span style="flex-shrink:0">\u2600\ufe0f <b>上午</b> '+a1+'</span>';
      h+='<span style="color:var(--text-muted,#999)">|</span>';
      h+='<span style="flex-shrink:0">\u2615 <b>下午</b> '+a2+'</span>';
      h+='<span style="color:var(--text-muted,#999)">|</span>';
      h+='<span style="flex-shrink:0">\u{1F319} <b>晚上</b> '+a3+'</span>';
      h+='</div></div>';
      dayNum++;
    }
  }
  h+='</div>';
  return h;
}

function mcToggleItin(ri){
  var el=document.getElementById("mcItin_"+ri);
  var arr=document.getElementById("mcArr_"+ri);
  if(!el) return;
  if(el.style.display==="none"||el.style.display===""){
    el.style.display="block";
    if(arr) arr.style.transform="rotate(90deg)";
  }else{
    el.style.display="none";
    if(arr) arr.style.transform="rotate(0deg)";
  }
}

// ── Step 6: Review Popup ──
function showReviewPopup(dest) {
  var existing = document.getElementById("reviewPopup");
  if (existing) { existing.remove(); return; }

  var popup = document.createElement("div");
  popup.id = "reviewPopup";
  popup.className = "review-popup";
  popup.onclick = function(e) { if (e.target === popup) popup.remove(); };
  popup.innerHTML = '<div class="review-popup-inner" onclick="event.stopPropagation()">'
    + '<button class="close" onclick="document.getElementById(\'reviewPopup\').remove()">&times;</button>'
    + '<h3 style="margin:0 0 5px">' + dest + ' \u7684\u8bc4\u4ef7</h3>'
    + '<div id="reviewPopupContent" style="margin-top:10px"><div class="loading">\u52a0\u8f7d\u4e2d...</div></div>'
    + '<div style="text-align:center;margin-top:12px">'
    + '<button onclick="showReviewForm(\'' + dest.replace(/'/g, "\\'") + '\')" style="background:#667eea;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer">\u5199\u8bc4\u4ef7</button>'
    + '</div></div>';
  document.body.appendChild(popup);

  loadReviewData(dest);
}

function loadReviewData(dest, page, sort) {
  page = page || 1;
  sort = sort || "newest";
  var x = new XMLHttpRequest();
  x.open("GET", "/api/reviews?destination=" + encodeURIComponent(dest) + "&page=" + page + "&limit=6&sort=" + sort, true);
  x.onload = function() {
    if (x.status !== 200) {
      document.getElementById("reviewPopupContent").innerHTML = '<div style="text-align:center;padding:20px;color:#999;font-size:14px">\u52a0\u8f7d\u5931\u8d25</div>';
      return;
    }
    try {
      var data = JSON.parse(x.responseText);
      renderReviewList(dest, data, page, sort);
    } catch(e) {
      document.getElementById("reviewPopupContent").innerHTML = '<div style="text-align:center;padding:20px;color:#999;font-size:14px">\u6570\u636e\u89e3\u6790\u5931\u8d25</div>';
    }
  };
  x.send();

  // Load stats
  var xs = new XMLHttpRequest();
  xs.open("GET", "/api/reviews/stats?destination=" + encodeURIComponent(dest), true);
  xs.onload = function() {
    if (xs.status === 200) {
      try {
        var st = JSON.parse(xs.responseText);
        renderReviewStats(st);
      } catch(e) {}
    }
  };
  xs.send();
}

function renderReviewStats(stats) {
  if (!stats || !document.getElementById("reviewPopupStats")) return;
  var h = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">';
  h += '<div style="text-align:center"><div style="font-size:28px;font-weight:700;color:#f59e0b">' + stats.avg_rating + '</div><div style="font-size:12px;color:var(--text-muted,#999)">' + renderStars(stats.avg_rating) + '</div><div style="font-size:10px;color:var(--text-muted,#999)">' + stats.total_count + '\u6761\u8bc4\u4ef7</div></div>';
  // Distribution bars
  h += '<div style="flex:1">';
  var stars = ["5", "4", "3", "2", "1"];
  for (var si = 0; si < stars.length; si++) {
    var s = stars[si];
    var pct = (stats.distribution && stats.distribution[s] != null) ? (stats.distribution[s] * 100) : 0;
    h += '<div style="display:flex;align-items:center;gap:4px;margin:2px 0;font-size:10px">';
    h += '<span style="width:14px">' + s + '\u2605</span>';
    h += '<div style="flex:1;height:6px;background:var(--bg-score,#f3f4f6);border-radius:3px;overflow:hidden"><div style="height:100%;width:' + pct + '%;background:#f59e0b;border-radius:3px"></div></div>';
    h += '<span style="width:28px;text-align:right;color:var(--text-muted,#999)">' + Math.round(pct) + '%</span></div>';
  }
  h += '</div></div>';
  document.getElementById("reviewPopupStats").innerHTML = h;
}

function renderReviewList(dest, data, page, sort) {
  var el = document.getElementById("reviewPopupContent");
  if (!el) return;

  var h = '<div style="margin-bottom:8px">';
  // Sort options
  h += '<div style="display:flex;gap:8px;font-size:11px;margin-bottom:6px">';
  var sorts = [{"v": "newest", "l": "\u6700\u65b0"}, {"v": "highest", "l": "\u6700\u9ad8\u5206"}, {"v": "lowest", "l": "\u6700\u4f4e\u5206"}];
  for (var si = 0; si < sorts.length; si++) {
    var active = (sorts[si].v === (sort || "newest"));
    h += '<span onclick="loadReviewData(\'' + dest.replace(/'/g, "\\'") + '\',1,\'' + sorts[si].v + '\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;background:' + (active ? '#667eea' : 'var(--bg-score,#f3f4f6)') + ';color:' + (active ? '#fff' : 'var(--text-secondary,#555)') + '">' + sorts[si].l + '</span>';
  }
  h += '</div></div>';

  // Stats container
  h += '<div id="reviewPopupStats"></div>';

  // Tag cloud
  h += '<div id="reviewPopupTags" style="margin:6px 0;display:flex;gap:4px;flex-wrap:wrap"></div>';

  // Reviews
  if (!data.reviews || data.reviews.length === 0) {
    h += '<div style="text-align:center;padding:20px;color:#999;font-size:14px">\u6682\u65e0\u8bc4\u4ef7</div>';
  } else {
    for (var ri = 0; ri < data.reviews.length; ri++) {
      var rv = data.reviews[ri];
      var types = {"solo": "\u72ec\u81ea", "couple": "\u60c5\u4fa3\u6e38", "family": "\u5bb6\u5ead\u6e38", "friends": "\u670b\u53cb\u6e38"};
      var typeLabel = types[rv.traveler_type] || rv.traveler_type;
      h += '<div class="review-item">';
      h += '<div style="display:flex;justify-content:space-between;align-items:center">';
      h += '<div><span style="font-weight:600;font-size:13px">' + renderStars(rv.rating) + '</span><span style="font-size:11px;color:var(--text-muted,#999);margin-left:4px">' + rv.user + '</span></div>';
      h += '<div style="font-size:10px;color:var(--text-muted,#999)">' + typeLabel + ' \u00b7 ' + rv.date + '</div></div>';
      h += '<div style="font-size:12px;color:var(--text-secondary,#555);margin:4px 0">' + escapeHtml(rv.content) + '</div>';
      if (rv.tags && rv.tags.length > 0) {
        h += '<div style="display:flex;gap:4px;flex-wrap:wrap">';
        for (var ti = 0; ti < rv.tags.length; ti++) {
          h += '<span style="font-size:10px;padding:2px 6px;background:#f3f4f6;border-radius:4px;color:#666">#' + rv.tags[ti] + '</span>';
        }
        h += '</div>';
      }
      h += '</div>';
    }
  }

  // Pagination
  if (data.total_pages > 1) {
    h += '<div style="display:flex;justify-content:center;gap:6px;margin-top:10px;font-size:12px">';
    for (var pi = 1; pi <= Math.min(data.total_pages, 5); pi++) {
      var active = pi === (page || 1);
      h += '<span onclick="loadReviewData(\'' + dest.replace(/'/g, "\\'") + '\',' + pi + ',\'' + (sort || "newest") + '\')" style="cursor:pointer;padding:3px 10px;border-radius:4px;background:' + (active ? '#667eea' : 'var(--bg-score,#f3f4f6)') + ';color:' + (active ? '#fff' : 'var(--text-secondary,#555)') + '">' + pi + '</span>';
    }
    h += '<span style="font-size:11px;color:#999;padding:3px 4px">\u2026</span>';
    h += '</div>';
  }

  el.innerHTML = h;
}

// ── Step 7: Write Review Form ──
var _reviewTypes = ["solo", "couple", "family", "friends"];
var _reviewTypeLabels = {"solo": "\u72ec\u81ea\u6e38", "couple": "\u60c5\u4fa3\u6e38", "family": "\u5bb6\u5ead\u6e38", "friends": "\u670b\u53cb\u6e38"};

function showReviewForm(dest) {
  var existing = document.getElementById("reviewFormPopup");
  if (existing) { existing.remove(); return; }

  var popup = document.createElement("div");
  popup.id = "reviewFormPopup";
  popup.className = "review-popup";
  popup.onclick = function(e) { if (e.target === popup) popup.remove(); };
  popup.innerHTML = '<div class="review-popup-inner" onclick="event.stopPropagation()" style="max-width:440px">'
    + '<button class="close" onclick="document.getElementById(\'reviewFormPopup\').remove()">&times;</button>'
    + '<h3 style="margin:0 0 15px">\u5199\u8bc4\u4ef7</h3>'
    
    + '<div style="font-size:12px;color:var(--text-muted,#999);margin-bottom:8px">\u76ee\u7684\u5730</div>'
    + '<div id="rfDest" style="font-size:14px;font-weight:600;margin-bottom:12px">' + dest + '</div>'

    + '<div style="font-size:12px;color:var(--text-muted,#999);margin-bottom:6px">\u8bc4\u5206</div>'
    + '<div id="rfStars" style="display:flex;gap:4px;margin-bottom:12px">'
    + '<span class="rf-star" data-v="1" onclick="setReviewStar(1)" style="font-size:28px;cursor:pointer;color:#ccc">\u2605</span>'
    + '<span class="rf-star" data-v="2" onclick="setReviewStar(2)" style="font-size:28px;cursor:pointer;color:#ccc">\u2605</span>'
    + '<span class="rf-star" data-v="3" onclick="setReviewStar(3)" style="font-size:28px;cursor:pointer;color:#ccc">\u2605</span>'
    + '<span class="rf-star" data-v="4" onclick="setReviewStar(4)" style="font-size:28px;cursor:pointer;color:#ccc">\u2605</span>'
    + '<span class="rf-star" data-v="5" onclick="setReviewStar(5)" style="font-size:28px;cursor:pointer;color:#ccc">\u2605</span>'
    + '</div>'

    + '<div style="font-size:12px;color:var(--text-muted,#999);margin-bottom:6px">\u51fa\u6e38\u7c7b\u578b</div>'
    + '<div id="rfType" style="display:flex;gap:6px;margin-bottom:12px">'
    + '<span class="rf-type-btn" data-v="solo" onclick="setReviewType(\'solo\')" style="cursor:pointer;padding:4px 10px;border-radius:6px;font-size:12px;background:var(--bg-score,#f3f4f6)">\u72ec\u81ea\u6e38</span>'
    + '<span class="rf-type-btn" data-v="couple" onclick="setReviewType(\'couple\')" style="cursor:pointer;padding:4px 10px;border-radius:6px;font-size:12px;background:var(--bg-score,#f3f4f6)">\u60c5\u4fa3\u6e38</span>'
    + '<span class="rf-type-btn" data-v="family" onclick="setReviewType(\'family\')" style="cursor:pointer;padding:4px 10px;border-radius:6px;font-size:12px;background:var(--bg-score,#f3f4f6)">\u5bb6\u5ead\u6e38</span>'
    + '<span class="rf-type-btn" data-v="friends" onclick="setReviewType(\'friends\')" style="cursor:pointer;padding:4px 10px;border-radius:6px;font-size:12px;background:var(--bg-score,#f3f4f6)">\u670b\u53cb\u6e38</span>'
    + '</div>'

    + '<div style="font-size:12px;color:var(--text-muted,#999);margin-bottom:6px">\u8bc4\u4ef7\u5185\u5bb9</div>'
    + '<textarea id="rfContent" maxlength="300" placeholder="\u8bf4\u8bf4\u4f60\u7684\u65c5\u884c\u4f53\u9a8c..." style="width:100%;box-sizing:border-box;border:1px solid var(--border-card,#e2e8f0);border-radius:6px;padding:8px;font-size:13px;height:80px;resize:vertical;font-family:inherit;margin-bottom:12px"></textarea>'
    + '<div style="text-align:right;font-size:10px;color:#999;margin-top:-10px;margin-bottom:8px"><span id="rfCount">0</span>/300</div>'

    + '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">'
    + '<span class="rf-tag-add" onclick="addReviewTag(\'\u6027\u4ef7\u6bd4\u9ad8\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;font-size:11px;border:1px dashed #ccc;color:#666">+\u6027\u4ef7\u6bd4\u9ad8</span>'
    + '<span class="rf-tag-add" onclick="addReviewTag(\'\u9002\u5408\u4eb2\u5b50\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;font-size:11px;border:1px dashed #ccc;color:#666">+\u9002\u5408\u4eb2\u5b50</span>'
    + '<span class="rf-tag-add" onclick="addReviewTag(\'\u7f8e\u98df\u591a\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;font-size:11px;border:1px dashed #ccc;color:#666">+\u7f8e\u98df\u591a</span>'
    + '<span class="rf-tag-add" onclick="addReviewTag(\'\u98ce\u666f\u7f8e\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;font-size:11px;border:1px dashed #ccc;color:#666">+\u98ce\u666f\u7f8e</span>'
    + '<span class="rf-tag-add" onclick="addReviewTag(\'\u4ea4\u901a\u4fbf\u5229\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;font-size:11px;border:1px dashed #ccc;color:#666">+\u4ea4\u901a\u4fbf\u5229</span>'
    + '<span class="rf-tag-add" onclick="addReviewTag(\'\u670d\u52a1\u597d\')" style="cursor:pointer;padding:3px 8px;border-radius:4px;font-size:11px;border:1px dashed #ccc;color:#666">+\u670d\u52a1\u597d</span>'
    + '</div>'
    
    + '<div id="rfTags" style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px"></div>'

    + '<div style="font-size:12px;color:var(--text-muted,#999);margin-bottom:6px">\u6635\u79f0</div>'
    + '<input id="rfUser" type="text" placeholder="\u4f60\u7684\u6635\u79f0" maxlength="10" style="width:100%;box-sizing:border-box;border:1px solid var(--border-card,#e2e8f0);border-radius:6px;padding:8px;font-size:13px;margin-bottom:15px">'

    + '<div style="display:flex;gap:6px">'
    + '<button onclick="submitReview()" style="flex:1;background:#667eea;color:#fff;border:none;border-radius:8px;padding:10px;font-size:14px;cursor:pointer">\u63d0\u4ea4\u8bc4\u4ef7</button>'
    + '<button onclick="document.getElementById(\'reviewFormPopup\').remove()" style="flex:1;background:var(--bg-score,#f3f4f6);color:var(--text-secondary,#555);border:none;border-radius:8px;padding:10px;font-size:14px;cursor:pointer">\u53d6\u6d88</button>'
    + '</div>'
    + '</div>';

  document.body.appendChild(popup);

  // Init state
  _formState = {dest: dest, rating: 0, type: "solo", tags: []};
  document.querySelector('[data-v="solo"]').style.background = "#667eea";
  document.querySelector('[data-v="solo"]').style.color = "#fff";

  // Character count
  document.getElementById("rfContent").oninput = function() {
    document.getElementById("rfCount").textContent = this.value.length;
  };
}

var _formState = {dest: "", rating: 0, type: "solo", tags: []};

function setReviewStar(v) {
  _formState.rating = v;
  var stars = document.querySelectorAll(".rf-star");
  stars.forEach(function(el, i) {
    el.style.color = (i < v) ? "#f59e0b" : "#ccc";
  });
}

function setReviewType(v) {
  _formState.type = v;
  var btns = document.querySelectorAll(".rf-type-btn");
  btns.forEach(function(el) {
    if (el.getAttribute("data-v") === v) {
      el.style.background = "#667eea";
      el.style.color = "#fff";
    } else {
      el.style.background = "var(--bg-score,#f3f4f6)";
      el.style.color = "var(--text-secondary,#555)";
    }
  });
}

function addReviewTag(tag) {
  if (_formState.tags.indexOf(tag) >= 0) return;
  _formState.tags.push(tag);
  renderReviewTags();
}

function removeReviewTag(tag) {
  _formState.tags = _formState.tags.filter(function(t) { return t !== tag; });
  renderReviewTags();
}

function renderReviewTags() {
  var el = document.getElementById("rfTags");
  if (!el) return;
  var h = "";
  _formState.tags.forEach(function(t) {
    h += '<span style="display:inline-flex;align-items:center;gap:3px;padding:3px 8px;background:#667eea;color:#fff;border-radius:4px;font-size:11px">#' + t + '<span style="margin-left:3px;opacity:.7;cursor:pointer" onclick="removeReviewTag(\u0027' + t + '\u0027)">&times;</span></span>';
  });
  el.innerHTML = h;
}

function submitReview() {
  var content = document.getElementById("rfContent").value.trim();
  var user = document.getElementById("rfUser").value.trim() || "\u533f\u540d\u7528\u6237";
  if (_formState.rating === 0) {
    showToast("\u8bf7\u9009\u62e9\u8bc4\u5206", "warning");
    return;
  }
  if (!content) {
    showToast("\u8bf7\u586b\u5199\u8bc4\u4ef7\u5185\u5bb9", "warning");
    return;
  }

  var payload = {
    destination: _formState.dest,
    user: user,
    rating: _formState.rating,
    content: content,
    traveler_type: _formState.type,
    tags: _formState.tags,
    date: new Date().getFullYear() + "-" + String(new Date().getMonth() + 1).padStart(2, "0"),
    budget_range: "",
    photos: []
  };

  var x = new XMLHttpRequest();
  x.open("POST", "/api/reviews", true);
  x.setRequestHeader("Content-Type", "application/json");
  x.onload = function() {
    try {
      var d = JSON.parse(x.responseText);
      if (d.status === "ok") {
        showToast("\u8bc4\u4ef7\u63d0\u4ea4\u6210\u529f! \u8c22\u8c22\u4f60\u7684\u5206\u4eab \u{1F389}", "success");
        var popup = document.getElementById("reviewFormPopup");
        if (popup) popup.remove();
        // Re-fetch review data if popup is open
        loadReviewData(_formState.dest, 1, "newest");
      } else {
        showToast("\u63d0\u4ea4\u5931\u8d25: " + (d.message || "\u672a\u77e5\u9519\u8bef"), "error");
      }
    } catch(e) {
      showToast("\u63d0\u4ea4\u5931\u8d25", "error");
    }
  };
  x.onerror = function() {
    showToast("\u7f51\u7edc\u9519\u8bef", "error");
  };
  x.send(JSON.stringify(payload));
}

// ═══════════════════════════════════════════
// ── POI 景点搜索（独立于原系统）──
// ═══════════════════════════════════════════

// POI 搜索按钮事件
(function() {
  var btn = document.getElementById("poiSearchBtn");
  if (!btn) return;
  btn.addEventListener("click", function(e) {
    doPOISearch(1);
  });
  // Enter 键触发
  document.getElementById("poiQ")?.addEventListener("keydown", function(e) {
    if (e.key === "Enter") doPOISearch(1);
  });
})();

// 页面加载时加载筛选器选项
(function() {
  // 从 API 获取筛选器选项
  fetch("/api/poi-search?q=&limit=1")
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (!d.meta) return;
      var citySel = document.getElementById("poiCity");
      var typeSel = document.getElementById("poiType");
      if (citySel && d.meta.cities) {
        d.meta.cities.forEach(function(c) {
          var opt = document.createElement("option");
          opt.value = c; opt.textContent = c;
          citySel.appendChild(opt);
        });
      }
      if (typeSel && d.meta.types) {
        d.meta.types.forEach(function(t) {
          var opt = document.createElement("option");
          opt.value = t; opt.textContent = t;
          typeSel.appendChild(opt);
        });
      }
    })
    .catch(function() {});
})();

function doPOISearch(page) {
  var btn = document.getElementById("poiSearchBtn");
  var resEl = document.getElementById("poiResults");
  var pagEl = document.getElementById("poiPagination");
  var statsEl = document.getElementById("poiStats");
  if (!btn || !resEl) return;
  
  btn.classList.add("loading");
  resEl.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted)">⏳ 搜索中...</div>';
  if (pagEl) pagEl.style.display = "none";

  var q = document.getElementById("poiQ")?.value || "";
  var city = document.getElementById("poiCity")?.value || "";
  var type = document.getElementById("poiType")?.value || "";
  var limit = document.getElementById("poiLimit")?.value || 20;

  var url = "/api/poi-search?q=" + encodeURIComponent(q)
    + "&city=" + encodeURIComponent(city)
    + "&dest_type=" + encodeURIComponent(type)
    + "&page=" + (page || 1)
    + "&limit=" + limit;

  var xhr = new XMLHttpRequest();
  xhr.open("GET", url, true);
  xhr.onload = function() {
    btn.classList.remove("loading");
    if (xhr.status !== 200) {
      resEl.innerHTML = '<div class="card"><div class="empty-msg"><div class="ek">❌</div>服务器错误: ' + xhr.status + '</div></div>';
      return;
    }
    var data;
    try { data = JSON.parse(xhr.responseText); } catch(e) {
      resEl.innerHTML = '<div class="card"><div class="empty-msg"><div class="ek">❌</div>数据解析错误</div></div>';
      return;
    }
    renderPOIResults(data, page || 1);
  };
  xhr.onerror = function() {
    btn.classList.remove("loading");
    resEl.innerHTML = '<div class="card"><div class="empty-msg"><div class="ek">❌</div>网络连接失败</div></div>';
  };
  xhr.send();
}

function renderPOIResults(data, currentPage) {
  var resEl = document.getElementById("poiResults");
  var pagEl = document.getElementById("poiPagination");
  var statsEl = document.getElementById("poiStats");
  if (!resEl) return;

  var items = data.results || [];
  var total = data.total || 0;
  var pages = data.pages || 1;

  // 更新统计
  if (statsEl) {
    var q = document.getElementById("poiQ")?.value || "";
    if (q) {
      statsEl.textContent = "找到 " + total + " 个相关景点（共 " + (data.meta?.total_destinations || total) + " 条）";
    } else {
      var count = data.meta?.total_destinations || total;
      statsEl.innerHTML = "共 <strong>" + count.toLocaleString() + "</strong> 个景点数据，AI 智能描述";
    }
  }

  if (items.length === 0) {
    resEl.innerHTML = '<div class="card"><div class="empty-msg"><div class="ek">🏝</div>未找到匹配的景点<br>试试其他关键词或减少筛选条件</div></div>';
    if (pagEl) pagEl.style.display = "none";
    return;
  }

  var html = '';
  for (var i = 0; i < items.length; i++) {
    var d = items[i];
    var name = d.name_cn || d.name || "未知";
    var city = d.city || "";
    var type = d.dest_type || "";
    var desc = d.description || "暂无描述";
    var rating = d.rating || 0;
    var addr = d.address || "";
    var coords = d.coords || {};
    var keywords = d.keywords || [];
    
    // 城市标签颜色
    var cityColors = {"上海":"#667eea","浙江":"#10b981","江苏":"#f59e0b","广东":"#ef4444","四川":"#8b5cf6"};
    var cityColor = cityColors[city] || "#667eea";
    
    var kwHtml = '';
    for (var j = 0; j < Math.min(keywords.length, 4); j++) {
      kwHtml += '<span style="display:inline-block;padding:1px 7px;border-radius:8px;font-size:10px;background:var(--bg-score,#f3f4f6);color:#667eea;margin:1px 3px 1px 0">' + escapeHtml(keywords[j]) + '</span>';
    }

    // 如果搜索关键词匹配，高亮
    var qVal = (document.getElementById("poiQ")?.value || "").trim();
    var displayName = name;
    var displayDesc = desc;
    if (qVal) {
      var re = new RegExp(escapeRegExp(qVal), "gi");
      displayName = name.replace(re, function(m) { return "<mark style='background:#ffd700;color:#333;padding:0 2px;border-radius:2px'>" + m + "</mark>"; });
      displayDesc = desc.replace(re, function(m) { return "<mark style='background:#ffd700;color:#333;padding:0 2px;border-radius:2px'>" + m + "</mark>"; });
    }

    html += '<div class="result-card" style="border-left-color:' + cityColor + '">';
    html += '  <div style="display:flex;justify-content:space-between;align-items:flex-start">';
    html += '    <div style="flex:1">';
    html += '      <div style="font-size:16px;font-weight:600;color:var(--text-primary);margin-bottom:4px">' + displayName + '</div>';
    if (city || type) {
      html += '      <div style="font-size:12px;color:var(--text-secondary);margin-bottom:6px">';
      if (city) html += '<span style="display:inline-block;background:' + cityColor + ';color:#fff;padding:1px 8px;border-radius:4px;font-size:11px;margin-right:6px">' + escapeHtml(city) + '</span>';
      if (type) html += '<span style="display:inline-block;background:var(--bg-score,#f3f4f6);color:var(--text-secondary);padding:1px 8px;border-radius:4px;font-size:11px">' + escapeHtml(type) + '</span>';
      if (rating > 0) html += '<span style="margin-left:8px;color:var(--amber);font-size:12px">⭐ ' + rating.toFixed(1) + '</span>';
      html += '      </div>';
    }
    html += '      <div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin:6px 0">' + displayDesc + '</div>';
    if (kwHtml) html += '      <div>' + kwHtml + '</div>';
    if (addr) html += '      <div style="font-size:11px;color:var(--text-muted);margin-top:4px">📍 ' + escapeHtml(addr) + '</div>';
    if (coords && coords.lat) {
      html += '      <div style="font-size:10px;color:var(--text-muted);margin-top:2px">🌐 ' + coords.lat.toFixed(4) + ', ' + (coords.lng || 0).toFixed(4) + '</div>';
    }
    html += '    </div>';
    // POI → 推荐按钮
    if (city) {
      html += '  <div style="padding:8px 12px;border-top:1px solid var(--border-default)">';
      html += '    <button class="poi-to-recommend" onclick="goToRecommendFromPOI(\'' + escapeHtml(city) + '\')" style="width:100%;padding:8px;background:var(--accent);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:13px">';
      html += '      \ud83c\udfaf \u67e5\u770b ' + escapeHtml(city) + ' \u63a8\u8350\u65b9\u6848';
      html += '    </button>';
      html += '  </div>';
    }
    html += '</div>';
    html += '</div>';
  }

  resEl.innerHTML = html;

  // ── Task 1: 城市天气/评分信息注入 ──
  setTimeout(function() { injectCityWeatherToPOI(items); }, 100);

  // 分页
  if (pagEl && pages > 1) {
    pagEl.style.display = "block";
    var pagHtml = '<div style="display:flex;gap:6px;justify-content:center;align-items:center;flex-wrap:wrap">';
    // 上一页
    if (currentPage > 1) {
      pagHtml += '<button onclick="doPOISearch(' + (currentPage - 1) + ')" style="padding:6px 12px;border:1px solid var(--border-default);border-radius:6px;background:var(--bg-card);color:var(--text-primary);cursor:pointer;font-size:13px">‹ 上一页</button>';
    }
    // 页码
    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(pages, startPage + 4);
    for (var p = startPage; p <= endPage; p++) {
      var active = p === currentPage;
      pagHtml += '<button onclick="doPOISearch(' + p + ')" style="padding:6px 12px;border:1px solid ' + (active ? 'var(--accent)' : 'var(--border-default)') + ';border-radius:6px;background:' + (active ? 'var(--accent)' : 'var(--bg-card)') + ';color:' + (active ? '#fff' : 'var(--text-primary)') + ';cursor:pointer;font-size:13px;font-weight:' + (active ? '600' : '400') + '">' + p + '</button>';
    }
    // 下一页
    if (currentPage < pages) {
      pagHtml += '<button onclick="doPOISearch(' + (currentPage + 1) + ')" style="padding:6px 12px;border:1px solid var(--border-default);border-radius:6px;background:var(--bg-card);color:var(--text-primary);cursor:pointer;font-size:13px">下一页 ›</button>';
    }
    pagHtml += '<span style="font-size:12px;color:var(--text-muted);margin-left:8px">共 ' + total + ' 条，' + pages + ' 页</span>';
    pagHtml += '</div>';
    pagEl.innerHTML = pagHtml;
  } else if (pagEl) {
    pagEl.style.display = "none";
  }
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// ═══════════════════════════════════════════
// ── Task 1: POI 结果注入城市天气/评分 ──
// ═══════════════════════════════════════════

var _cityBriefCache = {};

function injectCityWeatherToPOI(items) {
  var cards = document.querySelectorAll("#poiResults .result-card");
  if (!cards.length || !items.length) return;
  
  // 收集当前页面所有城市
  var cities = {};
  var cardCities = [];
  for (var i = 0; i < items.length; i++) {
    var city = items[i].city || "";
    if (city && !cities[city]) {
      cities[city] = true;
      cardCities.push({city: city, cardIdx: i});
    }
  }
  
  // 为每个城市获取天气/评分
  cardCities.forEach(function(cc) {
    var c = cc.city;
    if (_cityBriefCache[c]) {
      _applyCityBriefToCards(c, _cityBriefCache[c], items, cards);
      return;
    }
    fetch("/api/poi/city-brief?city=" + encodeURIComponent(c))
      .then(function(r) { return r.json(); })
      .then(function(data) {
        _cityBriefCache[c] = data;
        _applyCityBriefToCards(c, data, items, cards);
      })
      .catch(function() {});
  });
}

function _applyCityBriefToCards(city, data, items, cards) {
  if (!data || !data.found) return;
  var w = data.weather || {};
  
  // 找到所有该城市的卡片并注入
  for (var i = 0; i < items.length; i++) {
    if (items[i].city !== city) continue;
    var card = cards[i];
    if (!card) continue;
    // 避免重复注入
    if (card.querySelector(".city-brief-section")) continue;
    
    var briefHtml = '<div class="city-brief-section" style="margin-top:8px;padding:8px 10px;background:var(--bg-card-alt,#f8f9ff);border-radius:8px;font-size:12px;line-height:1.5">';
    briefHtml += '<div style="display:flex;flex-wrap:wrap;gap:4px 10px">';
    // 天气
    if (w.hi != null) {
      briefHtml += '<span>🌤 ' + w.lo + '~' + w.hi + '°C';
      if (w.rain != null) briefHtml += ' 💧' + w.rain + 'mm';
      if (w.comfort != null) {
        var stars = '';
        for (var s = 0; s < Math.round(w.comfort); s++) stars += '⭐';
        briefHtml += ' ' + stars;
      }
      briefHtml += '</span>';
    }
    // 评分
    if (data.rating != null && data.rating > 0) {
      briefHtml += '<span>⭐ ' + data.rating.toFixed(1) + ' (' + (data.rating_count || 0).toLocaleString() + ' 条评价)</span>';
    }
    // 价格
    if (data.hotel_range) {
      briefHtml += '<span>🏨 ¥' + data.hotel_range[0] + '-' + data.hotel_range[2] + '</span>';
    }
    if (data.food_range) {
      briefHtml += '<span>🍜 ¥' + data.food_range[0] + '-' + data.food_range[2] + '</span>';
    }
    briefHtml += '</div></div>';
    
    card.insertAdjacentHTML("beforeend", briefHtml);
  }
}

// ═══════════════════════════════════════════
// ── Task 2: 推荐卡片注入热门景点 ──
// ═══════════════════════════════════════════

function injectPOISections(results) {
  if (!results || !results.length) return;
  var cards = document.querySelectorAll(".result-card");
  
  for (var i = 0; i < results.length; i++) {
    var cityName = results[i].name_cn || results[i].name || "";
    if (!cityName) continue;
    var card = cards[i];
    if (!card || card.querySelector(".poi-card-section")) continue;
    
    // 从城市名提取主要城市（去除括号内容如 "上海 (Shanghai)"）
    var cleanCity = cityName.split(" (")[0].split("/")[0].trim();
    
    var sec = document.createElement("div");
    sec.className = "poi-card-section";
    sec.innerHTML = '<div class="poi-card-header" onclick="togglePOISection(this)" style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;padding:8px 0 4px;font-size:13px;color:var(--accent,#667eea);font-weight:500;border-top:1px solid var(--border-default,#eee)">'
      + '<span>🏛️ ' + escapeHtml(cleanCity) + '热门景点 ▸</span>'
      + '<span style="font-size:11px;color:var(--text-muted)">展开查看</span>'
      + '</div>'
      + '<div class="poi-card-body" style="display:none" data-city="' + escapeHtml(cleanCity) + '" data-loaded="false"></div>';
    card.appendChild(sec);
  }
}

function togglePOISection(headerEl) {
  var body = headerEl.parentElement.querySelector(".poi-card-body");
  if (!body) return;
  var open = body.style.display !== "none";
  body.style.display = open ? "none" : "block";
  var span = headerEl.querySelector("span:first-child");
  if (span) span.innerHTML = open ? ("🏛️ " + escapeHtml(body.dataset.city) + "热门景点 ▸") : ("🏛️ " + escapeHtml(body.dataset.city) + "热门景点 ▾");
  
  if (!open && body.dataset.loaded === "false") {
    _loadPOIForCity(body.dataset.city, body);
  }
}

// ── 天气预警弹窗 ──
function showWeatherModal() {
  var modal = document.getElementById('weatherModal');
  var list = document.getElementById('weatherModalList');
  // Collect weather warnings from current results
  var warnings = [];
  if (currentResults && currentResults.length > 0) {
    for (var i = 0; i < currentResults.length; i++) {
      var r = currentResults[i];
      if (r.weather_warnings && r.weather_warnings.length > 0) {
        for (var w = 0; w < r.weather_warnings.length; w++) {
          warnings.push({
            city: r.name_cn || r.name,
            level: r.weather_warnings[w].level || 1,
            icon: r.weather_warnings[w].icon || '⚠️',
            label: r.weather_warnings[w].label || '天气预警',
            msg: r.weather_warnings[w].msg || ''
          });
        }
      }
    }
  }
  if (warnings.length === 0) {
    list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">暂无天气预警 ☀️</div>';
  } else {
    var html = '';
    for (var i = 0; i < warnings.length; i++) {
      var w = warnings[i];
      html += '<div class="weather-modal-item"><span class="weather-modal-city">' + escapeHtml(w.city) + '</span>'
        + '<span class="weather-modal-badge warn-badge warn-' + w.level + '">' + w.icon + ' ' + escapeHtml(w.label) + '</span>'
        + '<span class="weather-modal-msg">' + escapeHtml(w.msg) + '</span></div>';
    }
    list.innerHTML = html;
  }
  modal.classList.add('active');
}

// ── 航班面板（占位） ──
function showFlightPanel() {
  showToast('✈️ 航班追踪功能即将更新');
}

// ── 评价面板（占位） ──
function showReviewPanel() {
  showToast('⭐ 评价系统功能即将更新');
}

// ── 更新天气角标 ──
function updateWeatherBadge() {
  var btn = document.getElementById('weatherBtn');
  if (!btn) return;
  var count = 0;
  if (currentResults && currentResults.length > 0) {
    for (var i = 0; i < currentResults.length; i++) {
      var r = currentResults[i];
      if (r.weather_warnings && r.weather_warnings.length > 0) {
        count += r.weather_warnings.length;
      }
    }
  }
  btn.dataset.count = count;
  btn.title = count > 0 ? count + ' 个天气预警' : '无天气预警';
}

// ── 页面初始化 ──
document.addEventListener('DOMContentLoaded', function() {
  initTabs();
  updateWeatherBadge();
});

function _loadPOIForCity(city, bodyEl) {
  if (!city || !bodyEl || bodyEl.dataset.loading === "1") return;
  bodyEl.dataset.loading = "1";
  bodyEl.innerHTML = '<div style="text-align:center;padding:12px;font-size:12px;color:var(--text-muted)">⏳ 加载中...</div>';
  
  fetch("/api/poi-search?city=" + encodeURIComponent(city) + "&limit=5")
    .then(function(r) { return r.json(); })
    .then(function(data) {
      bodyEl.dataset.loaded = "true";
      bodyEl.dataset.loading = "";
      var pois = data.results || [];
      if (pois.length === 0) {
        bodyEl.innerHTML = '<div style="padding:10px;font-size:12px;color:var(--text-muted);text-align:center">暂无收录该城市的具体景点</div>';
        return;
      }
      var html = '';
      for (var i = 0; i < pois.length; i++) {
        var p = pois[i];
        var pName = p.name_cn || p.name || "未知";
        var pDesc = (p.description || "").substring(0, 60) + "...";
        var pType = p.dest_type || "";
        var colorMap = {"主题乐园":"#e85d04","古镇/乡村":"#7f2d2d","人文历史":"#7209b7","度假休闲":"#0096c7","海岛/海滨":"#0077b6","自然风光":"#2d6a4f","都市休闲":"#3a0ca3"};
        var tColor = colorMap[pType] || "#667eea";
        html += '<div style="padding:6px 8px;border-left:3px solid ' + tColor + ';background:var(--bg-card-alt,#f8f9ff);border-radius:6px;margin-bottom:6px">';
        html += '  <div style="display:flex;justify-content:space-between;align-items:center">';
        html += '    <strong style="font-size:13px;color:var(--text-primary)">' + escapeHtml(pName) + '</strong>';
        if (pType) html += '    <span style="font-size:10px;color:' + tColor + ';background:' + tColor + '22;padding:1px 6px;border-radius:4px">' + escapeHtml(pType) + '</span>';
        html += '  </div>';
        html += '  <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;line-height:1.5">' + escapeHtml(pDesc) + '</div>';
        html += '</div>';
      }
      html += '<div style="font-size:11px;color:var(--text-muted);text-align:right;margin-top:2px">共 ' + (data.total || pois.length) + ' 个景点 <a href="#" onclick="switchToPOITab(event,\'" + escapeHtml(city) + "\')" style="color:var(--accent,#667eea);text-decoration:none">在搜景点中查看全部 →</a></div>';
      bodyEl.innerHTML = html;
    })
    .catch(function() {
      bodyEl.dataset.loaded = "true";
      bodyEl.dataset.loading = "";
      bodyEl.innerHTML = '<div style="padding:10px;font-size:12px;color:var(--red);text-align:center">❌ 加载失败</div>';
    });
}

function switchToPOITab(e, city) {
  e.preventDefault();
  // 切换到 POI 搜索选项卡
  document.getElementById("poiQ").value = "";
  document.getElementById("poiCity").value = city;
  document.getElementById("poiType").value = "";
  document.getElementById("poiCard").scrollIntoView({behavior: "smooth"});
  // 自动搜索
  doPOISearch(1);
}

// 挂钩到 postRender
(function() {
  var origPostRender = window.postRender;
  if (typeof origPostRender === "function") {
    window.postRender = function(results, dep) {
      origPostRender(results, dep);
      // 美团注入和 POI 注入互不影响
      setTimeout(function() { injectPOISections(results); }, 300);
    };
  }
})();