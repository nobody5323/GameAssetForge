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
- 扩展 CORS，支持 Vite dev server `http://127.0.0.1:5173`

## 功能描述

本 PR 完成素材生成主链路的第一版闭环。用户在前端填写素材需求后，可以直接点击 `GENERATE ASSETS`，后端会先编译提示词，再通过 Mock Provider 生成本地 PNG 文件，最后把素材记录持久化到本地 JSON 仓库。

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
15 passed
```

前端：

```bash
cd frontend
npm test
npm run build
```

已验证：

```text
4 test files, 12 tests passed
vite build completed
```

真实 HTTP 联调：

```text
POST http://127.0.0.1:8000/api/assets/generate
Origin: http://127.0.0.1:5173
```

已验证返回：

```json
{
  "status": 200,
  "cors": "http://127.0.0.1:5173",
  "provider": "mock",
  "assetCount": 1,
  "localPath": "runtime/storage/generated-assets/{generationId}/enemy/bamboo_slime.png"
}
```

浏览器验证：

- Vite 页面可挂载
- 页面显示 `GENERATE ASSETS`
- 页面默认目标模型为 `Mock Seed`
- 浏览器控制台无 React 挂载错误

## 依赖与来源说明

- 本 PR 不新增第三方依赖。
- 后端继续使用 FastAPI、Pydantic、pytest。
- 前端继续使用 React、Vite、Vitest、lucide-react。
- mock PNG 生成与复制沿用 PR6 的本地 provider，不调用外部生图 API。
