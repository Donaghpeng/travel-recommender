# 🗺️ 功能清单（Functional Map）

> 旅行推荐系统完整功能目录  
> 用途：防止 AI 助手改代码时「误删/误改」未知功能  
> 规则：**每个功能有明确的前端入口 + 后端 API + 数据依赖**  
> 版本：v1.0（基于代码审计 2026-06-22）

---

## 一、核心推荐系统

### F1：目的地推荐搜索 ⭐ P0

| 项目 | 详情 |
|:----|:------|
| **用户入口** | 推荐 Tab → 搜索表单 → 点击「搜索目的地」 |
| **前端函数** | `doSearch()` (事件绑定在 HTML 的 searchBtn) → `renderResults()` → `postRender()` |
| **后端 API** | `GET /api/recommend?budget=&days=&travel_date=&departure=&preferences=&travelers=&region=` |
| **响应格式** | `{"results": [...], "input": {...}}`，results 中是 5 个目的地对象 |
| **关键字段** | `name`, `name_cn`, `total_score`, `scores: {cost,route,review,weather,preference}`, `type`, `ai_blurb`, `weather_detail`, `weather_warnings`, `review_summary`, `estimate`, `itinerary`, `booking_links`, `poi_list` |
| **数据依赖** | `TravelRecommender.recommend()` → 58 个目的地 → 5 维评分 |
| **状态** | ✅ 稳定，不可修改非新增部分 |

### F2：预览卡片 → 详情抽屉 ⭐ P0

| 项目 | 详情 |
|:----|:------|
| **用户入口** | 搜索结果 → 预览卡片网格 → 点击「查看详情」或卡片 → 右侧滑入抽屉 |
| **前端函数** | `renderResults()` 渲染预览卡 → 点击调用 `openDrawer()` → `renderDrawer(idx)` 填充抽屉内容 |
| **后端 API** | 纯前端，数据来自 F1 的 `results` 数组 |
| **抽屉内容** | AI 描述 → 评分总览（进度条）→ 展开交通/酒店/餐饮 → 行程规划 → 航班信息 → 用户评价 → POI 推荐 → 预订链接 |
| **状态** | ✅ 稳定，CSS 在 index.html L198-209 |

### F3：搜索结果多选（对比/标记）⭐ P2

| 项目 | 详情 |
|:----|:------|
| **用户入口** | 预览卡片右上角圆圈 → 点击切换选中状态 |
| **前端函数** | `toggleSel(idx, circle)` → 维护 `selectedIdx[]` → `openCompare()` |
| **状态** | ⚠️ `openCompare()` 仍存在但对比弹窗已移除（EXECUTION_STEPS Step 10），`selectedIdx` 仅用于显示标签 |

---

## 二、POI 景点系统

### F4：POI 关键词搜索 ⭐ P0

| 项目 | 详情 |
|:----|:------|
| **用户入口** | POI Tab → 搜索表单 → 点击「搜景点」 |
| **前端函数** | `doPOISearch(page)` → `renderPOIResults(data, page)` |
| **后端 API** | `GET /api/poi-search?q=&city=&dest_type=&page=&limit=` |
| **响应格式** | `{"results": [...], "total": N, "page": 1, "limit": 20, "pages": M, "meta": {cities, types}}` |
| **数据依赖** | `data/enriched_ai.json`（7.6MB，懒加载）→ 10,997 POI |
| **状态** | ✅ 稳定，不可修改核心逻辑 |

### F5：POI 结果注入城市天气/评分 ⭐ P1

| 项目 | 详情 |
|:----|:------|
| **用户入口** | POI 搜索后 → 每条结果卡片底部自动显示城市天气/评分/价格 |
| **前端函数** | `renderPOIResults()` 末尾 `setTimeout` 调 `injectCityWeatherToPOI(items)` → `_applyCityBriefToCards(city, data, items, cards)` |
| **后端 API** | `GET /api/poi/city-brief?city=杭州` |
| **缓存** | `_cityBriefCache = {}` (JS 内存缓存) |
| **降级策略** | 58 个目的地中查找 → 降级 POI 坐标纬度估算 |
| **状态** | ✅ 稳定 |

### F6：POI → 推荐跳转 ⭐ P1

| 项目 | 详情 |
|:----|:------|
| **用户入口** | POI 结果卡片底部 → 点击「🎯 查看杭州推荐方案」 |
| **前端函数** | `goToRecommendFromPOI(city)` → 设置偏好 → `switchTab("recommend")` → 点击 searchBtn |
| **后端 API** | 复用 F1 |
| **状态** | ✅ 已实现（app.js L156-173），但可能存在：搜索结果页不会自动高亮目标城市 |

### F7：推荐卡片底部 POI 折叠区 ⭐ P1

| 项目 | 详情 |
|:----|:------|
| **用户入口** | 推荐结果卡片底部 → 展开「🏛️ 热门景点」 |
| **前端函数** | `postRender()` → `injectPOISections(results)` → `togglePOISection(headerEl)` → `_loadPOIForCity(city, bodyEl)` |
| **后端 API** | 复用 F4（内部调用 `/api/poi-search?city=杭州&limit=5`） |
| **状态** | ✅ 稳定 |

---

## 三、多城市联游 🔴 部分缺失

### F8：联游方案生成 ⚠️ 注意

| 项目 | 详情 |
|:----|:------|
| **用户入口** | 原本：推荐结果上方「联游方案」按钮 → 展示联游方案 |
| **前端函数** | `showMultiCityCard()` → 插入到 `#results`（推荐 Tab 的结果区域上方） |
| **后端 API** | `GET /api/multi-city?budget=&days=&departure=&preferences=&travelers=` |
| **响应格式** | `{"routes": [...], "input": {...}, "recommended_cities": [...]}` |
| **数据依赖** | `route_planner.recommend_routes()` |
| **问题** | **联游 Tab 容器存在（`#tab-multi`）但为空占位符**，`showMultiCityCard()` 插入到推荐 Tab 而非联游 Tab。联游功能在 Tab 重构（Step 1-5）后未正确迁移。 |

| **状态** | ✅ **已修复** — `showMultiCityCard()` 现在插入到 `#multiResults`（联游 Tab），切 Tab 时自动触发 |

### F9：联游方案详情渲染 ✅

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `mcRenderCard()` → `mcSVGRoute()` / `mcCityImgCard()` / `mcBudgetBar()` / `mcRiskSection()` / `mcItinerary()` |
| **依赖** | `_mcRoutes[]` 全局变量，`mcLoadCityImgs()` 加载图片 |
| **状态** | ✅ 渲染函数完整，随 F8 自动调用 |

---

## 四、航班追踪系统

### F10：航班价格估算 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/flight/estimate?departure=&destination=&travel_date=` |
| **状态** | ✅ 稳定 |

### F11：航班批量追踪 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/flight/track?departure=&destinations=` → `batch_track()` |
| **状态** | ✅ 稳定 |

### F12：价格趋势数据 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/flight/trend?departure=&destination=&travel_date=&days=` |
| **生成** | 历史不足 3 条时合成 30 天虚拟数据 |
| **状态** | ✅ 稳定 |

### F13：低价提醒 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/flight/set-alert` / `my-alerts` / `check-alerts` / `remove-alert` |
| **状态** | ✅ 稳定 |

### F14：搜索结果价格趋势 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `postRender()` → `addPriceTrends(rs, dep)` → `fetchTrend(dep, dest, elId)` → `showTrend(data, elId)` |
| **后端 API** | `GET /api/flight/track-search?departure=&destinations=` |
| **状态** | ✅ 稳定 |

---

## 五、评价系统

### F15：评价查询 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/reviews?destination=&page=&limit=&sort=&traveler_type=` |
| **状态** | ✅ 稳定 |

### F16：评价统计 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/reviews/stats?destination=` |
| **状态** | ✅ 稳定 |

### F17：评价提交 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `POST /api/reviews` (body: `{destination, rating, content, traveler_type, tags}`) |
| **状态** | ✅ 稳定 |

### F18：评价弹窗（前端）⭐ P2

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `showReviewPopup(dest)` → `loadReviewData(dest, page, sort)` → `renderReviewStats(stats)` / `renderReviewList(dest, data, page, sort)` |
| **状态** | ✅ 稳定 |

### F19：评价提交表单（前端）⭐ P2

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `showReviewForm(dest)` → `setReviewStar()` / `setReviewType()` / `submitReview()` |
| **状态** | ✅ 稳定 |

---

## 六、天气系统

### F20：天气预警 ⭐ P1

| 项目 | 详情 |
|:----|:------|
| **用户入口** | ⚠️ 工具栏按钮 → 弹窗展示各城市预警 |
| **前端函数** | `showWeatherModal()` → 从 `currentResults` 提取 `weather_warnings` → 渲染列表 |
| **后端 API** | `GET /api/weather/warning?lat=&lon=&month=` (独立查询) |
| **状态** | ✅ 稳定 |

### F21：后台天气 Enrich ⭐ P1

| 项目 | 详情 |
|:----|:------|
| **后端函数** | `_enrich_weather()` → 调用 `compute_monthly_avg()` → 覆写 cache |
| **状态** | ✅ 稳定 |

---

## 七、辅助功能

### F22：目的地图片 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/dest-image?name=&name_cn=&dest_type=` |
| **状态** | ✅ 稳定 |

### F23：目的地图片加载（前端）⭐ P2

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `loadDestImages(rs)` → 为每个目的地加载/设置图片 |
| **状态** | ✅ 稳定 |

### F24：出行小贴士 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `showTravelTips(rs)` |
| **状态** | ✅ 稳定 |

### F25：预订链接 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `addBookingButtons(results)` → `showBooking(dest, btnId, popupId)` |
| **后端 API** | `GET /api/booking?departure=&destination=&travel_date=` |
| **状态** | ✅ 稳定 |

### F26：携程出行清单 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/ctrip/checklist` |
| **状态** | ✅ 稳定 |

### F27：地理编码 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/geocode?address=` |
| **状态** | ✅ 稳定 |

### F28：高德地图配置 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/amap-config` → 返回 key + secret |
| **状态** | ✅ 稳定（但暴露硬编码密钥，需改进） |

### F29：反馈 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/feedback?dest=&helpful=&score=...` / `GET /api/feedback/stats` |
| **状态** | ✅ 稳定 |

### F30：三层记忆（Short/Medium/Long Term）⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /api/memory/short` / `/api/memory/medium` / `/api/memory/long` / `/api/memory` |
| **状态** | ✅ 稳定 |

### F31：健康检查 ⭐ P3

| 项目 | 详情 |
|:----|:------|
| **后端 API** | `GET /health` → `{"status": "ok"}` |
| **状态** | ✅ 稳定 |

---

## 八、页面级功能

### F32：Tab 导航切换 ⭐ P0

| 项目 | 详情 |
|:----|:------|
| **前端函数** | `initTabs()` → `switchTab(tab)` |
| **状态管理** | `tabStates = { recommend: {...}, poi: {...}, multi: {...} }` |
| **状态** | ✅ 稳定 |

### F33：全局工具栏 ⭐ P1

| 项目 | 详情 |
|:----|:------|
| **位置** | HTML 底部固定（L411-416） |
| **按钮** | ⚠️ 天气预警 / ✈️ 航班面板 / ⭐ 评价面板 |
| **状态** | ✅ 稳定，但航班/评价面板目前显示 ToDo 占位消息 |

### F34：暗色主题 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **实现** | CSS 变量（:root），全暗色设计 |
| **状态** | ✅ 稳定（仅暗色，无亮色切换） |

### F35：高德地图 ⭐ P2

| 项目 | 详情 |
|:----|:------|
| **文件** | `static/js/map.js` |
| **用户入口** | 推荐结果上方地图区域 |
| **状态** | ✅ 稳定 |

---

## 九、已废弃/已移除的功能

以下功能在 EXECUTION_STEPS Phase 3 中计划移除，代码中可能仍有残留：

| 功能 | 残留位置 | 处理状态 |
|:----|:---------|:---------|
| **美团集成** | `app.py` L361-477（死代码）、`meituan_parser.py`（文件还在） | ❌ 未完全清理 |
| **导出 PDF** | `generatePDF()` 已移除 | ✅ 已清 |
| **对比弹窗** | `openCompare()` 仍存在但仅显示标签 | ⚠️ 部分清理 |
| **`_kill_process_tree()`** | `app.py` L401-421 | ❌ 死函数残留 |

---

## 十、修改规则

1. **F1-F5 的渲染函数不可重写核心逻辑** — 如需扩展，参考 `postRender()` 的钩子模式
2. **所有新功能追加在 `app.js` 末尾**，使用新函数名，不要嵌入旧的 `renderResults()`
3. **每个功能修改后必须运行 `smoke_test.py`** 确认未破坏其他功能
4. **后端 API 必须保持优雅降级**（try/catch + fallback）
5. **发现新功能/修复 → 立即更新此清单**

---

> 最后更新：2026-06-22 | 功能总计：35 项（P0: 4, P1: 6, P2: 12, P3: 8, ❌问题: 2）
