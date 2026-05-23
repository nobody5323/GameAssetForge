# PR 7: Asset Generation Service

## 新增/修改内容

- 新增 `POST /api/assets/generate`
  - 接收项目需求、素材列表、`promptMode` 和 `targetModel`
  - 返回 `generationId`、素材记录、本地路径、provider metadata 和提示词信息
- 新增 `AssetGenerationService`
  - 串联 Prompt Compiler、Mock Image Provider 和 Asset Repository
  - 默认使用第一套候选提示词进入 mock 素材生成
- 新增 `AssetRepository`
  - 使用本地 JSON 文件保存 generation 与 asset record
  - 运行时数据写入 `backend/runtime/storage/asset-db.json`
- 扩展 asset models
  - 新增 `AssetGenerateRequest`
  - 新增 `AssetGenerateResponse`
  - 新增 `AssetRecord`
- 前端生成页接入真实生成接口
  - `GENERATE ASSETS` 按钮调用 `/api/assets/generate`
  - 展示 `generationId`、素材名、类型、本地路径、provider 和 prompt hash
  - 默认目标模型改为 `Mock Seed`，保证无 API Key 也能演示
- 修复前端可见中文乱码
- 扩展 CORS，支持 Vite dev server `http://127.0.0.1:4173`、`http://127.0.0.1:4174`
- 新增后端静态文件挂载 `/runtime`，用于浏览器直接访问生成的 PNG 图片
- 新增前端 `buildAssetPreviewUrl()`，将后端 `localPath` 转为浏览器可加载的图片 URL
- 新增生成结果图片缩略图，`GeneratedAssetsPanel` 嵌入 `<img>` 标签展示素材预览
- 前端 Vite dev server 端口改为 4174，避免端口冲突

## 功能描述

本 PR 完成素材生成主链路的第一版闭环。用户在前端填写素材需求后，可以直接点击 `GENERATE ASSETS`，后端会先编译提示词，再通过 Mock Provider 生成本地 PNG 文件，最后把素材记录持久化到本地 JSON 仓库。生成的图片通过后端 `/runtime` 静态文件挂载点直接在浏览器中预览展示。

本 PR 不接入真实生图模型，仍使用 `mock_seed` 与 `MockImageProvider` 保证比赛演示时无 API Key 也能运行。

## 实现思路

- 后端采用 service orchestration：路由层只负责 HTTP 输入输出，`AssetGenerationService` 负责串联提示词、图片 provider 和仓库。
- Prompt Compiler 复用 PR5/PR6 已有逻辑，生成服务使用第一套候选提示词作为当前 MVP 的默认选择。
- Mock Provider 复用 PR6 的本地 PNG seed 复制逻辑，生成路径保持为 `runtime/storage/generated-assets/{generationId}/{assetType}/{assetName}.png`。
- Repository 使用 JSON 文件，便于 PR8 素材库直接读取，也便于调试和演示。
- 前端新增 `assetGeneration.js` API helper，把生成页和后端接口隔离，方便后续替换真实 provider 或接入素材库。

## 测试方式

后端：

```bash
cd backend
python -m pytest
```

已验证：

```text
16 passed
```

前端：

```bash
cd frontend
npx vitest run
npm run build
```

已验证：

```text
5 test files, 15 tests passed
vite build completed
```

真实 HTTP 联调：

```text
POST http://127.0.0.1:8000/api/assets/generate
Origin: http://127.0.0.1:4174
```

已验证返回：

```json
{
  "status": 200,
  "cors": "http://127.0.0.1:4174",
  "provider": "mock",
  "assetCount": 4,
  "localPath": "runtime/storage/generated-assets/{generationId}/enemy/bamboo_slime.png"
}
```

静态文件验证：

```bash
curl http://127.0.0.1:8000/runtime/storage/generated-assets/{generationId}/character/hero.png
# 返回 200，content-type: image/png
```

浏览器验证：

- Vite 页面可挂载，像素风暗色主题渲染正常
- 页面默认目标模型为 `Mock Seed`
- 点击 GENERATE ASSETS 后，生成结果面板展示 4 个素材卡片（含图片缩略图）
- 图片通过后端 `/runtime` 静态文件服务正确加载
- 候选提示词面板展示编译结果

## 依赖与来源说明

- 本 PR 不新增第三方依赖。
- 后端继续使用 FastAPI、Pydantic、pytest。
- 前端继续使用 React、Vite、Vitest、lucide-react。
- mock PNG 生成与复制沿用 PR6 的本地 provider，不调用外部生图 API。
