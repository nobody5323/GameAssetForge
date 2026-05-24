# PR11：Manifest 与 Zip 导出

## 新增/修改内容

- 新增：`backend/app/models/export_models.py` — Manifest、ManifestAsset、ExportResponse 数据模型
- 新增：`backend/app/services/export_service.py` — 导出服务（manifest 生成 + zip 打包）
- 新增：`backend/app/routes/export_routes.py` — 导出 API 路由
- 新增：`backend/tests/test_export_service.py` — 8 个导出测试
- 修改：`backend/app/models/asset_models.py` — AssetRecord 新增 `projectName` 字段
- 修改：`backend/app/services/asset_generation_service.py` — 持久化 projectName
- 修改：`backend/app/main.py` — 注册导出路由
- 修改：`frontend/src/assetGeneration.js` — 新增 `fetchExportableGenerations()` 和 `exportGeneration()`
- 修改：`frontend/src/assetGeneration.test.js` — 新增导出函数导出验证测试
- 修改：`frontend/src/App.jsx` — 重写 ExportPage 为动态导出页面
- 修改：`frontend/src/styles.css` — 新增导出页面样式

## 功能描述

本 PR 实现了素材包导出功能：为指定 generation 生成 `manifest.json` 并打包所有 PNG 素材为 zip 文件，通过浏览器直接下载。

### 后端

- `POST /api/exports/{generation_id}`：触发导出，返回 zip 文件流（Content-Type: application/zip, Content-Disposition: attachment）
- `GET /api/exports`：列出所有可导出的 generation ID
- ExportService 流程：
  1. 从 AssetRepository 读取指定 generation 的所有素材
  2. 对每个素材运行 QualityService 质量检查
  3. 生成 `manifest.json`（含素材名称、类型、风格、提示词、质量评分、zip 内路径）
  4. 使用 Python `zipfile` 模块将 manifest.json + 所有 PNG 文件打包
  5. 同时保存到 `backend/runtime/exports/` 目录供后续访问

### 前端

- ExportPage 从后端加载 generation 列表
- 下拉选择器 + 手动输入支持
- EXPORT ZIP 按钮触发导出并自动下载
- 导出结果卡片显示素材数、manifest 大小、总大小
- 涵盖 loading / empty / error 状态

## 实现思路

- 使用 Python 标准库 `zipfile` + `io.BytesIO` 实现内存中 zip 构建，无需第三方依赖
- manifest.json 采用 Pydantic 模型序列化，保证字段完整和类型安全
- 前端通过 `fetch` blob 响应 + `URL.createObjectURL` 触发浏览器下载
- AssetRecord 新增 `projectName` 字段，使 manifest 能正确标注项目名

## 测试方式

1. 执行 `cd backend && python -m pytest` — 42 测试全部通过
2. 执行 `cd frontend && npm test` — 16 测试全部通过
3. 执行 `cd frontend && npm run build` — Vite 生产构建成功
4. 手动测试：
   - 启动后端 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
   - 访问前端，先生成素材（Generate 页）
   - 切换到导出页面，选择 generation，点击 EXPORT ZIP
   - 验证浏览器下载的 zip 包含 manifest.json 和分类目录的 PNG 文件

## 依赖与来源说明

本 PR 是否引入第三方依赖：否（使用 Python 标准库 `zipfile`, `io`, `json`）
