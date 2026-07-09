# 🧭 旅行推荐系统

> **AI 驱动的旅行目的地推荐 + 景点搜索系统**  
> 基于 58 个精选目的地（城市级）+ 10,997 个具体景点（POI 级）双数据源  
> 运行在 `http://127.0.0.1:8000`，Windows 本地环境

---

## 目录

- [功能概述](#功能概述)
- [数据源](#数据源)
- [系统架构](#系统架构)
- [后端 API](#后端-api)
- [前端结构](#前端结构)
- [核心模块](#核心模块)
- [运行指南](#运行指南)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

---

## 功能概述

### 🎯 两大核心功能

#### 1. 目的地推荐（原系统）
- 基于 AI 多维度评分（天气、成本、路线、评价、偏好）为用户推荐适合的旅行目的地
- 覆盖 58 个国内外目的地（含中文地区、东南亚、日韩等）
- 每个目的地包含：天气信息、评分、价格预估、AI 描述、出行建议、旅游信息（美团）等
- 支持按预算、季节、出行类型、偏好筛选
- 支持对比分析、行程规划

#### 2. 景点搜索（POI 系统）
- 独立于推荐系统的景点级搜索，覆盖 10,997 个具体景点
- 支持关键词搜索、按城市/类型筛选、分页
- 每个景点有 AI 生成的描述、坐标、关键词标签
- 与推荐系统联动：
  - **POI → 推荐**：在 POI 搜索结果中展示该城市的天气、评分、价格等摘要信息
  - **推荐 → POI**：在推荐卡底部可展开查看该城市的热门景点列表

### 🖼️ 效果预览

| 功能 | 位置 | 说明 |
|---|---|---|
| 目的地搜索 | 页面顶部主卡片 | 搜索 58 个推荐目的地 |
| 景点搜索 | 页面下方"搜景点"卡片 | 搜索 10,997 个具体景点 |
| 城市天气卡片 | POI 搜索结果卡底部 | 自动显示城市天气/评分/价格 |
| 热门景点卡片 | 推荐结果卡底部的折叠区 | 展开查看城市景点列表 |
| 旅游信息 | 推荐结果卡底部的折叠区 | 美团酒旅数据 |
| 路线规划 | 侧边栏 | 多目的地路线 |
| 对比 | 结果上方 | 多目的地对比 |
| 地图 | 侧边栏 | 高德地图标记 |

---

## 数据源

### 数据集 A：58 个目的地（城市级，约 10KB/条）

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 英文名，如 "Hangzhou" |
| `name_cn` | str | 中文名，如 "杭州" |
| `dest_type` | str | 目的地类型：`City`/`Beach`/`Mountain`/`Historical`/`Island`/`Cultural`/`Nature` |
| `latitude/longitude` | float | 坐标 |
| `weather` | dict[str, list] | 月度天气，键为月份字符串，值为 `[高温, 低温, 雨量, 舒适度]` |
| `rating_overall` | float | AI 综合评分 |
| `rating_count` | int | 评价数 |
| `cost_hotel_per_night` | tuple | 住宿价格 `(淡季, 平季, 旺季)` |
| `cost_food_per_day` | tuple | 餐饮价格 `(淡季, 平季, 旺季)` |
| `cost_flight` | tuple | 机票价格 `(淡季, 平季, 旺季)` |
| `keywords` | list[str] | 关键词|
| `description` | str | 中文描述 |
| `region` | str | 区域：`Domestic`/`Southeast Asia`/`East Asia`/`South Asia` |

> **数据来源**：`destinations_data.py` + `reviews.db`（评价覆盖）  
> **中文名称映射**：`zh_names.py` 中的 `CN_NAMES` 字典

### 数据集 B：10,997 个 POI 景点（景点级，约 700B/条）

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 景点英文名 |
| `name_cn` | str | 景点中文名 |
| `city` | str | 所在城市，如 "杭州" |
| `province` | str | 所在省份，如 "浙江" |
| `dest_type` | str | 类型：`主题乐园`/`古镇/乡村`/`人文历史`/`度假休闲`/`海岛/海滨`/`自然风光`/`都市休闲` |
| `description` | str | AI 生成的中文描述（约 150-300 字）|
| `keywords` | list[str] | 关键词列表 |
| `latitude/longitude` | float | 景点的精确坐标 |
| `address` | str | 详细地址 |
| `rating` | float | 评分 (0-5) |

> **数据文件**：`data/enriched_ai.json`（7.6MB，懒加载）  
> **来源**：高德地图 POI + AI 增强描述

---

## 系统架构

### 请求流程图

```
用户输入 → [FastAPI /app.py] → TravelRecommender.recommend()
                                      ↓
                              缓存命中？ ← CacheManager
                              ↙         ↘
                            是           否
                          返回缓存     计算评分
                                       ↓
                                  缓存结果
                                  ↙  ↓  ↘
                           前台响应   后台 4 路异步 enrich：
                           （带缓存）     ↙  ↓  ↓  ↘
                                     AI 天气 评价 价格预警
```

### 同步 + 后台 Enrich 模式

这是系统核心模式：

1. 同步返回评分结果（毫秒级）
2. 后台 4 个守护线程并行工作：
   - `_enrich_ai()` — AI 描述生成（调用 DeepSeek）
   - `_enrich_weather()` — 实时天气数据（Open-Meteo）
   - `_track_results()` — 记录搜索日志
   - `_warn_weather()` — 天气预警
3. 后台结果**覆写同一缓存键**
4. 用户下次刷新时看到增强效果

⚠️ **首次请求通常没有 AI 描述和天气详情，刷新后即得完整信息。**

### 文件结构

```
travel-recommender/
├── app.py                     # FastAPI 主应用（后端入口）
├── travel_recommender.py      # 评分引擎核心
├── destinations_data.py       # 58 个目的地数据定义
├── zh_names.py                # 中英文名称映射表
├── weather_service.py         # 天气服务（Open-Meteo + 纬度估算）
├── memory.py                  # 长期记忆索引
├── cache_manager.py           # 缓存管理（LRU + TTL）
├── ai_writer.py               # AI 描述生成（DeepSeek API）
├── review_db.py               # 评价数据库管理
├── review_seed.py             # 评价数据填充
├── reviews_api.py             # 评价查询 API
├── ctrip_integration.py       # 携程旅行建议集成
├── meituan_parser.py          # 美团酒旅数据解析
├── flight_tracker.py          # 机票价格追踪
├── itinerary.py               # 行程规划
├── route_planner.py           # 路线规划
├── transport.py               # 交通信息
├── risk_checker.py            # 安全风险检查
├── currency.py                # 货币转换
├── models.py                  # 数据模型
├── budget_splitter.py         # 预算拆分
├── feedback.py                # 用户反馈
├── city_clusters.py           # 城市聚类
├── healthcheck.py             # 健康检查
│
├── data/                      # 数据文件
│   ├── enriched_ai.json       # 10,997 POI 景点数据（7.6MB）
│   └── result_cache.json      # 结果缓存持久化
│
├── static/                    # 前端（SPA，无构建步骤）
│   ├── index.html             # 主页面
│   ├── css/                   # 无独立 CSS，全部内联在 HTML 中
│   ├── js/
│   │   ├── app.js             # 主逻辑（约 80KB）
│   │   └── map.js             # 高德地图模块
│   └── img-hosting/           # 65 个目的地封面图
│
├── docs/
│   └── destination-expansion-plan.md  # 目的地扩展计划
│
└── tests/                     # 单元测试
    ├── test_recommender.py
    └── test_scoring.py
```

---

## 后端 API

### 推荐系统 API

| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/recommend?q=...&budget=...&season=...&pref=...` | **核心推荐**，多维度评分筛选 |
| GET | `/api/compare?ids=a,b,c` | 多目的地对比 |
| GET | `/api/flight/trend?dest=...&dep=...` | 机票价格趋势 |
| GET | `/api/route?from=...&to=...` | 路线规划 |
| GET | `/api/weather/warning?lat=...&lon=...` | 天气预警 |
| POST | `/api/feedback` | 提交反馈 |
| GET | `/api/meituan/cached?city=...` | 美团酒旅缓存数据 |
| GET | `/api/health` | 健康检查 |

### POI 景点搜索 API

| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/poi-search?q=&city=&dest_type=&page=1&limit=20` | **搜索景点** |
| GET | `/api/poi/city-brief?city=杭州` | **城市摘要**（天气+评分+价格） |

#### `/api/poi-search`

```json
GET /api/poi-search?q=西湖&city=杭州&limit=2

Response:
{
  "results": [
    { "name_cn": "西湖", "city": "杭州", "dest_type": "人文历史",
      "description": "...", "keywords": ["...",] "coords": {...} }
  ],
  "total": 69,
  "page": 1,
  "limit": 2,
  "pages": 35,
  "meta": {
    "total_destinations": 10997,
    "cities": ["上海","杭州","南京","成都", ...],
    "types": ["主题乐园","古镇/乡村","人文历史", ...]
  }
}
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `q` | string | `""` | 关键词，匹配景点名/描述/城市/关键词 |
| `city` | string | `""` | 按城市精确筛选 |
| `dest_type` | string | `""` | 按类型精确筛选 |
| `page` | int | `1` | 页码，≥1 |
| `limit` | int | `20` | 每页条数，1-100 |

**特性：**
- 数据懒加载：首次请求时才从磁盘加载 `enriched_ai.json`
- 关键词匹配优先级：描述 > 名称 > 城市 > 关键词
- 有关键词时按匹配度排序

#### `/api/poi/city-brief`

```json
GET /api/poi/city-brief?city=杭州

Response:
{
  "found": true,
  "city": "杭州",
  "weather": { "hi": 28, "lo": 20, "rain": 60, "comfort": 3.5 },
  "rating": 4.4,
  "rating_count": 36000,
  "hotel_range": [150, 250, 450],
  "food_range": [70, 110, 170],
  "flight_range": [200, 350, 600],
  "lat": 30.27,
  "lon": 120.15,
  "dest_type": "City"
}
```

**匹配逻辑：**
1. 精确匹配 `CN_NAMES` + `name` 字段
2. 模糊包含匹配（含"杭州"、"杭州 in 杭州 (China)" 等）
3. **降级**：若 58 个目的地中找不到（如苏州、上海），则从 POI 数据取坐标 + 纬度估算天气

---

## 前端结构

### 页面布局

```
┌─────────────────────────────────────────────────┐
│    🧭 搜索目的地           [关键词] [搜索]        │  ← 主搜索卡片
│    预算 | 季节 | 类型 | 天数 | 出发地 | 偏好       │
├─────────────────────────────────────────────────┤
│    ↓ 2-3 行对比按钮 / 地图 / 路线 / 收藏           │
├─────────────────────────────────────────────────┤
│    ┌─ 推荐卡片 1 ──────────────────────────────┐ │
│    │ 🌴 三亚  评分 4.5 | 住宿 ¥150-450          │ │
│    │ 🌤 28~26°C | 💧120mm | ✈️ ¥600-1200       │ │
│    │ [AI 描述] [评价] [天气详情]                  │ │
│    │ ├─ 🍜 旅游信息 ▸ [美团数据]                │ │  ← 折叠区
│    │ └─ 🏛️ 三亚热门景点 ▸ [POI 列表]           │ │  ← 折叠区
│    └───────────────────────────────────────────┘ │
│    ┌─ 推荐卡片 2 (同类) ──────────────────────┐ │
│    │ ...                                       │ │
│    └───────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│    🔎 搜景点                                      │  ← POI 搜索卡片
│    [关键词] [城市▼] [类型▼] [每页▼] [搜索]         │
│    ┌─ 景点卡片 ────────────────────────────────┐ │
│    │ 🏯 西湖  杭州 | 人文历史 | ⭐ 4.5            │ │
│    │ AI 描述文字...                             │ │
│    │ ─────────────────────────────────────     │ │
│    │ 🌤 28~20°C 💧60mm ⭐⭐⭐⭐                  │ │  ← 城市天气/评分卡片
│    │ ⭐ 4.4 (36,000 条) 🏨 ¥150-450 🍜 ¥70-170 │ │
│    └───────────────────────────────────────────┘ │
│    [分页: < 1 2 3 4 5 >]                         │
└─────────────────────────────────────────────────┘
```

### 关键 JS 函数

| 函数名 | 位置 | 说明 |
|---|---|---|
| `doSearch()` | `app.js` | 目的地搜索主入口 |
| `renderResults()` | `app.js` | 渲染搜索结果卡片 |
| `postRender()` | `app.js` | 渲染后处理（图片、价格趋势、旅行提示） |
| `doPOISearch(page)` | `app.js` | POI 景点搜索入口 |
| `renderPOIResults(data, page)` | `app.js` | 渲染 POI 搜索结果 |
| `injectCityWeatherToPOI(items)` | `app.js` | POI 卡片注入城市天气 |
| `_applyCityBriefToCards(...)` | `app.js` | 城市天气注入逻辑 |
| `injectPOISections(results)` | `app.js` | 推荐卡片注入热门景点折叠区 |
| `togglePOISection(headerEl)` | `app.js` | 切换热门景点展开/收起 |
| `_loadPOIForCity(city, bodyEl)` | `app.js` | 异步加载城市景点列表 |
| `switchToPOITab(e, city)` | `app.js` | 跳转到 POI 搜索选项卡 |
| `injectMeituanCards(results)` | `index.html` inline | 推荐卡片注入美团数据折叠区 |
| `escapeRegExp(string)` | `app.js` | 转义正则特殊字符 |
| `escapeHtml(str)` | `app.js` | 转义 HTML 特殊字符 |

### 设计原则

- **零外部 CDN** — 所有依赖静态加载，适用于 GFW 环境
- **无构建步骤** — 直接编辑 `static/js/app.js` 和 `static/index.html`
- **缓存破坏** — `<script src="js/app.js?v={timestamp}">` 自动更新
- **暗色模式** — 通过 `data-theme="dark"` CSS 变量切换
- **独立模块** — `app.js` 主逻辑 / `map.js` 高德地图

---

## 核心模块

### TravelRecommender（评分引擎）

`travel_recommender.py` 中 `TravelRecommender.recommend()` 的工作流程：

1. **5 维评分**：Cost / Route / Review / Weather / Preference
   - 每维度 1-5 分
2. **权重调整**：
   - `_adjust_weights()` 根据预算、季节、出行类型、天数、偏好、区域调整权重
   - 自动重新归一化至总和 1.0
3. **季节成本**：所有价格字段为 `(淡季, 平季, 旺季)` 三元组
   - 淡季：1,2,3,11,12 月
   - 平季：4,5,9,10 月
   - 旺季：6,7,8 月
4. **多样性**：`_diversify()` 使用 MMR（最大边际相关性）避免同类目的地过多
5. **无推荐兜底**：所有目的地评分后推荐前 5 名

### CacheManager（缓存）

`cache_manager.py`：
- 单例 `result_cache` + 独立 weather/geocode 缓存
- LRU 驱逐 + 每 5 分钟清理
- 文件持久化到 `data/result_cache.json`
- 支持异步 `aset()` / `aget()`（注意当前有 bug，正在修复）

### WeatherService（天气）

`weather_service.py`：
- **快速估算**：`_latitude_estimate(lat, month)` — 基于纬度估算月度天气
- **实时数据**：`get_forecast(lat, lon, days=7)` — Open-Meteo API
- **文件缓存**：`.weather_cache/` 目录
- **天气预警**：`check_weather_warnings()` 基于温度和降雨量

### LongTermMemory（长期记忆）

`memory.py`：
- 基于 numpy 的向量索引
- 存储 58 个目的地的高维向量表示
- `search(query_embedding, k)` 返回最相似目的地
- 启动时自动构建索引

---

## 运行指南

### 启动服务

```bash
cd C:\Users\Donaghy\Desktop\travel-recommender
python app.py
# → http://127.0.0.1:8000
```

或使用 uvicorn（热重载调试）：

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 运行测试

```bash
# 单元测试（无需服务）
python run_tests.py
pytest tests/ -v --tb=short

# 集成测试（需服务运行中）
python test_cache.py
```

### 依赖安装

```bash
pip install -r requirements.txt
pip install pytest   # 额外测试依赖
```

### 环境配置

`.env` 文件：
```
DEEPSEEK_KEY=your_key_here
```

---

## 开发指南

### 新增目的地

1. 在 `destinations_data.py` 的 `load_all()` 中添加目的地信息
2. 在 `zh_names.py` 的 `CN_NAMES` 中添加中英文映射
3. 添加封面图片到 `static/img-hosting/`

### 新增 POI 景点数据

编辑 `data/enriched_ai.json`，格式：

```json
{
  "name": "West Lake",
  "name_cn": "西湖",
  "city": "杭州",
  "province": "浙江",
  "dest_type": "人文历史",
  "description": "...",
  "keywords": ["西湖","杭州","湖","...],
  "coords": {"lat": 30.24, "lng": 120.15},
  "address": "浙江省杭州市西湖区龙井路1号",
  "rating": 4.8
}
```

### 修改前端

1. 修改 `static/index.html` 调整布局/样式
2. 修改 `static/js/app.js` 调整逻辑
3. 无需构建，刷新浏览器即可生效
4. 如果浏览器缓存了 JS，更新 `v=` 参数：`<script src="js/app.js?v={new_timestamp}">`

### 核心规则

- **不要修改 `renderResults()` / `doSearch()`** — 原推荐系统是稳定的
- 扩展功能应追加在 `app.js` 末尾，使用新函数
- `postRender()` 可安全包裹（见 `injectMeituanCards` 和 `injectPOISections` 的模式）
- 外部 API 调用必须有降级回退（`try/catch + 估算/硬编码`）
- 所有 API key 使用环境变量而非硬编码

### 集成模式

**推荐卡片注入**（例如添加新的折叠区到结果卡）：

```javascript
function injectMyFeature(results) {
  var cards = document.querySelectorAll(".result-card");
  for (var i = 0; i < results.length; i++) {
    var card = cards[i];
    var sec = document.createElement("div");
    sec.className = "my-feature-section";
    sec.innerHTML = '<div>...</div><div class="body" data-loaded="false"></div>';
    card.appendChild(sec);
  }
}

// 挂在 postRender 上
(function() {
  var orig = window.postRender;
  window.postRender = function(results, dep) {
    orig(results, dep);
    setTimeout(function() { injectMyFeature(results); }, 300);
  };
})();
```

---

## 常见问题

### Q: 页面打开后推荐结果没有 AI 描述和天气详情？

A: 这是正常的。首请求同步返回评分结果，后台异步生成 AI 描述和拉取天气。刷新页面（或等几秒后重新搜索）即可看到完整内容。

### Q: POI 搜索返回"基于纬度估算"的天气？

A: 58 个目的地只覆盖了 35 个中国城市 + 23 个国际目的地。如搜索苏州、上海等不在列表中的城市，系统自动从 POI 数据获取坐标并估算天气。数据准确度不如完整目的地数据，但提供基本参考。

### Q: 如何切换暗色模式？

A: 页面底部有主题切换按钮（☀️/🌙），或手动在浏览器控制台运行：
```javascript
document.documentElement.dataset.theme = 'dark';
```

### Q: 服务器启动报端口占用？

A: 8000 端口已被占用时，修改 `app.py` 最后一行的 `port=8000` 为其他端口。

### Q: 美团数据不显示？

A: 美团数据需要后台爬虫预先加载。第一次访问某个城市时显示"⏳ 正在查询..."，可能需要几分钟才能完成首次爬取。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+, FastAPI, uvicorn |
| 前端 | Vanilla JS（零框架、零构建） |
| 数据 | JSON, SQLite, numpy |
| 天气 | Open-Meteo API（免费，无需 Key）|
| 地图 | 高德地图 AMap API |
| AI 描述 | DeepSeek API (via `ai_writer.py`) |
| 评价数据 | `reviews.db` (SQLite) |
| 缓存 | LRU + 文件持久化 |
| 测试 | pytest |

---

*文档维护者：小比 🐾 · 最后更新：2026-06-16*
