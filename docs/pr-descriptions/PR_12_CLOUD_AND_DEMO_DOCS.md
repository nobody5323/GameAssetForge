# PR12：云端模拟上传与最终文档

## 新增/修改内容

- 新增：`backend/app/providers/cloud_provider.py` — CloudProvider 抽象接口 + CloudUploadResult
- 新增：`backend/app/providers/mock_cloud_provider.py` — MockCloudProvider 模拟云端上传
- 新增：`backend/app/services/cloud_service.py` — CloudService 上传编排
- 新增：`backend/app/routes/cloud_routes.py` — 云端上传 API 路由
- 新增：`backend/tests/test_cloud_service.py` — 7 个云端上传测试
- 修改：`backend/app/repositories/asset_repository.py` — 新增 `update_asset()` 和 `find_asset()`
- 修改：`backend/app/main.py` — 注册 cloud_router
- 修改：`frontend/src/assetGeneration.js` — 新增 `uploadAssetToCloud()` 和 `uploadGenerationToCloud()`
- 修改：`frontend/src/App.jsx` — ExportPage 新增云端上传区块
- 修改：`frontend/src/styles.css` — 新增 `.export-divider`、`.cloud-hint` 样式
- 修改：`README.md` — 全面重写：技术栈、API 表、快速开始、项目结构、验收清单
- 修改：`docs/DEMO_SCRIPT.md` — 更新为 6 段式详细演示脚本

## 功能描述

本 PR 是 12-PR MVP 的收尾 PR，完成三项工作：

### 1. 云端上传模拟

- CloudProvider 抽象层（与 ImageProvider 设计一致）
- MockCloudProvider：将文件复制到 `backend/runtime/mock-cloud/` 并返回 `cloud://mock/{asset_id}/{file}` 格式模拟 URL
- CloudService 上传后更新 AssetRecord.cloudUrl
- API：`POST /api/cloud/upload/{asset_id}` 和 `POST /api/cloud/upload-generation/{generation_id}`
- 前端导出页面集成：UPLOAD TO CLOUD 按钮 + 上传结果展示

### 2. 最终 README

- 完整技术栈说明
- 快速开始指南（含 Windows/macOS）
- API 端点表（11 个端点）
- 项目结构树
- 原创功能亮点（Prompt Compiler / Quality Inspector / Cloud Asset Hub）
- 验收清单全部勾选

### 3. Demo 脚本

- 6 段时间线（0:00-6:30）
- 覆盖全部核心流程：生成 → 编译 → 素材库 → 质检 → 上传 → 导出

## 实现思路

- CloudProvider 遵循与 ImageProvider 相同的抽象模式，方便后续扩展七牛云 / S3
- 模拟 URL 格式 `cloud://mock/...` 直观可辨
- AssetRepository 新增 `update_asset` / `find_asset` 方法支撑素材状态更新
- 前端复用 ExportPage 的 generation 选择器，上传与导出共用一个 selector

## 测试方式

1. `cd backend && python -m pytest` — 49 测试全部通过（含 7 个云端测试）
2. `cd frontend && npx vitest run` — 17 测试全部通过
3. `cd frontend && npm run build` — 生产构建成功
4. 手动端到端：
   - 启动后端 `uvicorn app.main:app --host 127.0.0.1 --port 8000`
   - 启动前端 `npm run dev`
   - 生成素材 → 导出 zip → 上传云端 → 查看 cloudUrl

## 依赖与来源说明

本 PR 是否引入第三方依赖：否（使用 Python 标准库 `shutil`、`abc`）
