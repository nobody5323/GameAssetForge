# PR 8: Asset Library 素材库

## 新增/修改内容

- 新增 `GET /api/assets` 后端接口，支持可选的 `?category=` 查询参数按素材类型过滤。
- 前端 `assetGeneration.js` 新增 `fetchAssets(category?)` helper，封装素材库 API 调用。
- 前端素材库页面重写为动态数据驱动：
  - 页面加载时从后端获取真实素材记录。
  - 显示素材缩略图（通过 `buildAssetPreviewUrl` 加载后端静态文件）。
  - 新增类型筛选栏：全部 / character / enemy / item / tileset / ui / background，每个筛选项显示该类型的素材数量。
  - 支持手动刷新按钮。
  - 完善的加载态、空态、错误态展示。
- 新增前端 CSS：filter chip 样式、素材库面板样式、缩略图 img 样式、provider/genId 小标签样式。
- 新增后端测试：覆盖全部列表、按类型过滤、空分类返回空数组、字段完整性。
- 新增前端测试：验证 `fetchAssets` 导出正确。

## 功能描述

本 PR 实现素材库浏览功能，让用户可以在素材库页面查看所有已生成的素材：

- `GET /api/assets` 返回所有素材记录（按生成时间倒序）。
- `GET /api/assets?category=character` 仅返回指定类型的素材。
- 前端素材库页面使用 filter chip 按钮切换类型，每个 chip 显示该类型的素材计数。
- 素材卡片展示：
  - 素材缩略图（从 `backend/runtime/storage/` 静态文件服务加载）。
  - 素材名称、类型、质量评分（暂为 `--`，PR9 接入真实评分）。
  - generationId 和 provider 标签。
- 无素材时显示明确的空态提示，引导用户先去生成页创建素材。
- 加载中显示 spinning loader，网络错误时显示错误信息。

## 实现思路

- 后端复用 PR7 已有的 `AssetRepository.list_assets()` 方法，路由层仅做 category 过滤。
- 前端 `LibraryPage` 使用 `useState` + `useEffect` 管理状态，category 变化时自动重新请求。
- Filter chip 按钮复用已有的 `assetTypes` 常量数组（character/enemy/item/tileset/ui/background），确保与生成页的类型选项一致。
- 缩略图 URL 复用 PR7 已有的 `buildAssetPreviewUrl()` 函数，无需额外后端改动。
- 过滤计数在前端通过 `reduce` 计算，避免额外 API 请求。
- CSS 新增 filter chip、library panel、缩略图 img 等样式，保持像素风暗色主题一致。

## 测试方式

后端：

```bash
cd backend
python -m pytest
```

已验证：

```text
19 passed
```

前端：

```bash
cd frontend
npx vitest run
npm run build
```

已验证：

```text
4 test files, 14 tests passed
vite build completed
```

接口人工验证：

```bash
# 先通过 generate 创建素材
curl -X POST http://127.0.0.1:8000/api/assets/generate \
  -H "Content-Type: application/json" \
  -d '{"projectName":"Test","gameType":"platformer","style":"pixel_art","theme":"test","description":"test","targetModel":"mock_seed","promptMode":"normal","assets":[{"type":"character","name":"hero","description":"main character"},{"type":"enemy","name":"slime","description":"a slime"}]}'

# 获取全部素材
curl http://127.0.0.1:8000/api/assets

# 按类型过滤
curl http://127.0.0.1:8000/api/assets?category=character
```

前端人工验证：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 4174
```

打开：

```text
http://127.0.0.1:4174/
```

检查：

- 切换到素材库页面，看到 filter chip 栏（全部、character、enemy、item、tileset、ui、background）。
- 若已生成素材，每个 chip 显示对应数量；点击 chip 过滤素材卡片。
- 素材卡片显示缩略图、名称、类型、generationId、provider。
- 若素材库为空，显示空态提示 "素材库为空，请先在生成页创建素材"。
- 点击 REFRESH 按钮重新加载。

## 依赖与来源说明

- 后端复用 PR7 已引入的 FastAPI、Pydantic、pytest。
- 前端复用 PR2/PR4 已引入的 React、Vite、lucide-react、Vitest。
- 不新增第三方依赖。
