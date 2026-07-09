# 🧭 旅行推荐系统 · 执行步骤清单

> 基于 NJ 确认的方案，分 4 个 Phase，共 12 步  
> **同意后执行**，每步完成后等待确认可按需暂停

---

## Phase 1：导航 + 卡片重构 ✅

### 步骤 1 ✅ — 重构页面 HTML 结构

**改动文件：** `static/index.html`

- **将原单页内容拆入 Tab 容器：**
  ```html
  <!-- 新增 Tab 导航栏 -->
  <div class="tab-bar">
    <button class="tab-btn active" data-tab="recommend">🎯 目的地推荐</button>
    <button class="tab-btn" data-tab="poi">🔍 景点探索</button>
    <button class="tab-btn" data-tab="multi">🌐 多城市联游</button>
  </div>
  ```
- **原主搜索卡片 → 放入 `tab-recommend` 容器**
- **原 POI 搜索卡片 → 放入 `tab-poi` 容器**（移除原来的独立卡片外层 div）
- **原多城市联游按钮 → 扩展为独立的 `tab-multi` 容器页面**（调用 `/api/multi-city` 直接展示方案列表）
- 原 MapWrap、Toasts、Modal 保持全局（所有 Tab 共享）

### 步骤 2 ✅ — 实现 Tab 切换 + 状态保持

- 写 `initTabs()` 函数：
  - 点击 Tab 按钮 → 切换 `.tab-content` 的显示/隐藏
  - 高亮当前 Tab 按钮
- **状态保持机制：**
  - 切换到某个 Tab 时，如果该 Tab 之前已有搜索结果且未被清除，保留 DOM
  - 推荐 Tab：记住当前 `currentResults`、`selectedIdx`
  - POI Tab：记住当前分页数据
- 每个 Tab 有独立的 `state` 对象，Tab 切换时不做 DOM 销毁

### 步骤 3 ✅ — 新增全局工具栏（替代浮动按钮）

- **工具栏内容（固定在顶部 Tab 栏右侧或底部固定条）：**
  ```
  ☀ 主题切换 | ⚠️ 3 天气预警 | ✈️ 航班面板 | ⭐ 评价面板
  ```
- 移除原有的浮动按钮（主题切换 + 🍜 美团按钮）
- 每个工具图标点击后展开对应内容

### 步骤 4 ✅ — 天气预警弹窗

- 点击 ⚠️ 图标 → 弹出 modal 展示所有城市的天气预警列表
- Modal 内容：按严重程度排序，显示等级（⚠️1/⚠️2）、城市名、预警描述
- 复用现有 `.modal-overlay` 样式

### 步骤 5 ✅ — 结果卡片重构为预览卡 + 侧滑抽屉

- **预览卡渲染（重写 `renderResults()`）：**
  - 改为 CSS 网格布局，`auto-fill, minmax(280px, 1fr)`
  - 每张预览卡仅展示：
    ```
    ┌──────────────────┐
    │ 🥇 杭州  ⭐ 8.8   │
    │ ━━━━━━━━━━━━━━━━ │
    │ 天气 ☀️  成本 8/10 │
    │ 路线 7/10 评价 9/10│
    │ 偏好 6/10          │
    │ [查看详情 →]       │
    └──────────────────┘
    ```
  - 天气预警小标签显示在预览卡右上角
  - 去掉 AI 大段描述、日行程、评价摘要、预订链接等

- **侧滑抽屉（新增 DOM + CSS）：**
  ```html
  <div class="drawer-overlay" id="drawerOverlay">
    <div class="drawer" id="drawer">
      <div class="drawer-header">
        <button class="drawer-close">✕</button>
        <span class="drawer-title">#1 杭州</span>
      </div>
      <div class="drawer-body">
        <!-- 内容由 JS 动态填充 -->
      </div>
    </div>
  </div>
  ```
  - 侧滑从右侧滑入，宽度约 50-60%（大屏）或 90%（小屏）
  - 所有次要信息分层展示（可折叠）

- **详情抽屉渲染（新增 `renderDrawer(cityIndex)` 函数）：**
  - 从上到下：
    1. **AI 精简描述**（2-3 句）
    2. **评分总览**（进度条形式）
    3. **⏬ 展开详情** — 交通/酒店/餐饮
    4. **⏬ 展开行程** — 日行程
    5. **⏬ 航班信息** — 价格追踪
    6. **⏬ 用户评价** — 评价摘要
    7. **POI 推荐** — 该城市热门景点
    8. **联游方案** — 关联的多城市路线
    9. **预订链接** — 底部

---

## Phase 2：POI ↔ 推荐打通

### 步骤 6 — POI 卡片增加「查看推荐」按钮

**改动文件：** `static/js/app.js` → `renderPOIResults()` 函数

- 在每条 POI 结果卡片底部添加：
  ```html
  <button class="poi-to-recommend" data-city="杭州">
    🎯 查看杭州推荐方案
  </button>
  ```
- 按钮使用城市名（从 POI 数据的 `city` 字段读取）

### 步骤 7 — 实现跳转逻辑

**改动文件：** `static/js/app.js`

- 点击 POI 推荐按钮 → 切换 Tab 到 `tab-recommend`
- 自动触发一次推荐搜索，参数为：
  - 出发地：保留当前表单值
  - 偏好：填入该城市名（如"杭州"）
  - 预算/天数/日期：保留当前表单值
- 推荐结果中，该城市卡片添加 **高亮标记** `🔍 你从「西湖」来到这里`
- 若推荐 Tab 已有搜索结果，保留之前状态，新增结果追加在后面

---

## Phase 3：功能清理

### 步骤 8 — 移除美团集成

**改动文件：** `static/index.html`、`static/js/app.js`、`app.py`

- **前端：**
  - 移除美团卡片 HTML
  - 移除 `toggleMeituan()`、`meituanSearch()`、`renderMeituanResult()`、`injectMeituanCards()`、`toggleMtCard()`、`loadMtForCity()`、`formatMeituanData()` 等函数
  - 移除 `postRender()` 中调用美团注入的代码
- **后端：**
  - 移除 `/api/meituan/query`、`/api/meituan/result/{task_id}`、`/api/meituan/cached` 等 8 条路由
  - 清理 `explore_meituan.py`、`meituan_parser.py` 相关导入

### 步骤 9 — 移除导出 PDF

**改动文件：** `static/js/app.js`

- 移除对比栏中的"导出 PDF"按钮
- 移除 `generatePDF()` 函数

### 步骤 10 — 对比分析降级

**改动文件：** `static/js/app.js`

- 预览卡中保留勾选框（用于标记感兴趣）
- 移除原有的 3 列对比弹窗（`openCompare()`、`compare-grid`）
- 替换为简单的"你已标记 X 个城市"标签
- 移除 `compareModal` 的 HTML

---

## Phase 4：打磨与优化

### 步骤 11 — 自适应列数 + 响应式调整

**改动文件：** `static/index.html`（CSS 区域）

- 预览卡网格 CSS：
  ```css
  .preview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
  ```
- 侧滑抽屉响应式：
  ```css
  .drawer {
    width: min(520px, 90vw);
  }
  ```

### 步骤 12 — 全局工具栏细化 + 航班/评价折叠面板

**改动文件：** `static/index.html` + `static/js/app.js`

- 航班追踪面板：点击 ✈️ 图标 → 展示当前推荐城市的航班价格汇总
- 评价面板：点击 ⭐ 图标 → 展示所有推荐城市的评价汇总
- 天气预警弹窗：点击 ⚠️ 图标 → modal 展示各城市天气警告

---

## 执行顺序可视化

```
Phase 1 (6 steps) ──────────────────────── 核心视觉改造
  Step 1  HTML 重构（Tab 容器化）
  Step 2  Tab 切换 + 状态保持
  Step 3  全局工具栏
  Step 4  天气预警弹窗
  Step 5  预览卡 + 侧滑抽屉     ← 最大工作量
  ── 可在此暂停检查视觉效果 ──

Phase 2 (2 steps) ──────────────────────── 交互打通
  Step 6  POI 按钮
  Step 7  跳转逻辑

Phase 3 (3 steps) ──────────────────────── 功能裁剪
  Step 8  移除美团
  Step 9  移除导出 PDF
  Step 10 对比降级

Phase 4 (2 steps) ──────────────────────── 打磨
  Step 11 响应式
  Step 12 面板细化
```

---

**共计 12 步，预估工作量最大的在 Step 5（卡片重构+侧滑抽屉），建议 Phase 1 完成后暂停审查一次。**

同意后我开始执行 Phase 1 的 Step 1 🐾
