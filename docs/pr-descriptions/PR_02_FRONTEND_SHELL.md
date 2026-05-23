# PR 2: 实现前端基础界面框架

## 新增/修改内容

- 新增 React + Vite 前端工程入口：
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `frontend/vite.config.js`
  - `frontend/index.html`
  - `frontend/src/main.jsx`
  - `frontend/src/App.jsx`
  - `frontend/src/styles.css`
- 删除 `frontend/.gitkeep`，因为前端目录已经有真实工程文件。
- 新增左侧导航和四个前端工作区视图：
  - 素材生成
  - 素材库
  - 质量报告
  - 导出交付
- 新增静态表单、Prompt 预览、素材卡片、质量检查项和导出占位区域。
- 重构为像素风深色工作台视觉，包括像素字体、霓虹状态、面板边框和素材卡片样式。
- 新增 `.claude/` 忽略规则，避免本地工具配置进入仓库。

## 功能描述

本 PR 实现 GameAsset Forge 的前端基础界面框架，用于承载后续素材生成、素材库展示、质量评分和导出交付功能。

本 PR 不接入后端 API，不实现真实素材生成逻辑，只完成可运行、可切换、可继续扩展的前端工作台壳层。

## 实现思路

- 使用 React + Vite 搭建轻量前端工程，保证本地启动和构建速度。
- 使用 `vite.config.js` 固定开发服务器到 `127.0.0.1:4173`，避免与旧的 `5173` 服务冲突。
- 使用 `useState` 管理当前视图状态，实现无需路由依赖的基础导航切换。
- 使用 `lucide-react` 提供导航和操作图标，让页面结构更清晰。
- 使用普通 CSS 变量组织像素风主题色、面板、按钮、素材卡片和响应式布局。
- 将四个核心业务页面先做成静态视图：
  - 生成页展示后续 PR4 会接入的输入表单结构；
  - 素材库展示后续 PR8 会接入的素材卡片布局；
  - 质量报告展示后续 PR10 会接入的检查项布局；
  - 导出页展示后续 PR11 会接入的 zip/manifest 导出入口。
- CSS 采用普通样式文件实现响应式布局，避免在 PR2 引入额外 UI 框架。

## 测试方式

1. 安装前端依赖：

   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器：

   ```bash
   npm run dev
   ```

   验证 Vite 输出类似：

   ```text
   Local: http://127.0.0.1:4173/
   ```

3. 打开浏览器访问：

   ```text
   http://127.0.0.1:4173/
   ```

4. 人工验证：
   - 左侧显示 GameAsset Forge 品牌区；
   - 左侧导航包含素材生成、素材库、质量报告、导出交付；
   - 点击每个导航项，右侧标题和内容区域会切换；
   - 素材生成页展示静态表单和 Prompt Preview；
   - 素材库页展示静态素材卡片；
   - 质量报告页展示质量检查项；
   - 导出交付页展示导出入口占位。

5. 构建验证：

   ```bash
   npm run build
   ```

   本 PR 已验证构建通过。

6. 本地 HTTP 稳定性验证：

   连续 3 次请求 `http://127.0.0.1:4173/`，确认返回内容包含 `GameAsset Forge` 和 `/src/main.jsx`，页面入口稳定存在。

## 依赖与来源说明

- 本 PR 引入前端依赖：
  - `react` / `react-dom`：用于构建前端界面；
  - `vite` / `@vitejs/plugin-react`：用于本地开发和构建；
  - `lucide-react`：用于界面图标。
- 未复用外部历史代码。
