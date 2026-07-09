// map.js — 高德地图集成模块
// 仅在 AMap API 加载后生效，否则静默跳过

var _amt = 0;

function initMap() {
  if (typeof AMap === "undefined") {
    _amt++;
    if (_amt < 10) setTimeout(initMap, 500);
    return;
  }
  window._mapObj = new AMap.Map("mapBox", {
    zoom: 5,
    center: [104, 35],
    mapStyle: "amap://styles/whitesmoke"
  });
}

function clearMapMk() {
  var ms = window._mapMk || [];
  for (var i = 0; i < ms.length; i++) ms[i].setMap(null);
  window._mapMk = [];
}

function showOnMap(rs, depCity) {
  if (!window._mapObj) {
    initMap();
    setTimeout(function() { showOnMap(rs, depCity); }, 800);
    return;
  }
  var w = document.getElementById("mapWrap");
  if (w) w.classList.add("active");
  clearMapMk();
  var mk = [],
    allPts = [];
  var bc = ["#ffd700", "#c0c0c0", "#cd7f32", "#667eea", "#667eea"];

  for (var i = 0; i < rs.length; i++) {
    var r = rs[i];
    if (!r.latitude || !r.longitude) continue;
    allPts.push([r.longitude, r.latitude]);
    var m = new AMap.Marker({
      position: [r.longitude, r.latitude],
      title: r.name,
      label: {
        content: '<span style="background:' + bc[i] + ';color:#333;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:700">#' + (i + 1) + '</span>',
        offset: new AMap.Pixel(0, -24)
      }
    });
    m.on("click", (function(idx) {
      return function() { highlightCard(idx); };
    })(i));
    m.setMap(window._mapObj);
    mk.push(m);
  }
  window._mapMk = mk;
  try {
    if (allPts.length) window._mapObj.setFitView(allPts, false, [60, 60, 60, 60]);
  } catch (e) {
    /* map fit failed - non-critical */
  }
}

function highlightCard(idx) {
  var cs = document.querySelectorAll(".result-card");
  if (cs[idx]) {
    cs[idx].scrollIntoView({ behavior: "smooth", block: "center" });
    cs[idx].style.boxShadow = "0 0 0 4px #667eea";
    setTimeout(function() { cs[idx].style.boxShadow = ""; }, 2000);
  }
}
