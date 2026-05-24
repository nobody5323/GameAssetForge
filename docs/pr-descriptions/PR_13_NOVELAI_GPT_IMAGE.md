# PR13：GPT Image 真实生图接口

> **⚠️ 说明：** 本文档原包含 NovelAI 相关内容，NovelAI 因生成效果不适合本项目游戏素材需求，已在后续 commit 中全部移除。本文档已更新为仅保留 GPT Image（OpenAI）部分。

## 新增/修改内容

### 后端
- **新增**：`backend/app/providers/gpt_image_provider.py` — GptImageProvider，调用 OpenAI Images API 生成图片
- **新增**：`backend/tests/test_gpt_image_provider.py` — 5 个 GPT Image Provider 测试
- **修改**：`backend/app/models/config_models.py` — 新增 `ImageGenProvider`、`ImageConfigUpdate`、`ImageConfigResponse` 模型
- **修改**：`backend/app/config.py` — 新增 `ImageRuntimeConfig` 运行时配置类，支持 OpenAI API Key
- **修改**：`backend/app/routes/config_routes.py` — 新增 `GET/PUT /api/config/image` 路由
- **修改**：`backend/app/services/asset_generation_service.py` — 新增 `_select_provider()` 方法，根据 `targetModel` 自动路由到 GPT Image / Mock Provider；无凭证时自动降级
- **修改**：`backend/app/models/asset_models.py` — `ImageGenerationRequest` 新增 `negativePrompt` 字段
- **修改**：`backend/app/main.py` — CORS 新增 `5173` 端口（Vite dev server）

### 前端
- **新增**：`frontend/src/imageConfig.js` — Image API 配置助手：Provider 选项、模型选项、尺寸/画质选项、API 读写函数
- **修改**：`frontend/src/App.jsx` — 新增 "Image API 配置" 导航页；新增 `ImageConfigPage` 组件
- **修改**：`frontend/src/styles.css` — 新增 `.image-config-hint` 使用说明样式

### 配置
- **修改**：`.env.example` — 新增 `IMAGE_GEN_PROVIDER`、`IMAGE_GEN_BASE_URL`、`IMAGE_GEN_MODEL`、`IMAGE_GEN_SIZE`、`IMAGE_GEN_QUALITY`、`IMAGE_GEN_API_KEY` 环境变量

## 功能描述

本 PR 在 Mock Provider 基础上接入 OpenAI 真实 AI 生图接口：

### GPT Image Provider (OpenAI)

- 调用 OpenAI Images API (`POST /v1/images/generations`)
- 支持 GPT Image 2、DALL-E 3、DALL-E 2 模型
- DALL-E 模型支持 `standard` / `hd` 画质选择
- 支持 `b64_json` 响应格式，解码后存为本地 PNG
- 记录 `revisedPrompt`（DALL-E 3 自动改写后的 prompt）到 metadata
- 无 API Key 时自动降级到 Mock Provider

### 前端 Image API 配置页

- 新增独立配置页 "Image API 配置"
- 支持 OpenAI 模型选择（GPT Image 2 / DALL-E 3 / DALL-E 2）+ 尺寸 + 画质（DALL-E 专属）
- 支持自定义 Base URL 和 HTTP 代理
- LOAD / SAVE CONFIG 按钮

### Provider 路由机制

```
targetModel: "gpt_image" → GptImageProvider (有 key) / MockImageProvider (降级)
targetModel: "mock_seed" → MockImageProvider (始终)
```

## 实现思路

- GptImageProvider 继承 `ImageProvider` 抽象类，与 MockImageProvider 接口一致
- `AssetGenerationService._select_provider()` 根据 `request.targetModel` 选择对应的 provider，无凭证时降级为 Mock
- `ImageRuntimeConfig` 设计参考 `LlmRuntimeConfig`，支持 env / local JSON 文件双层配置
- 前端 ImageConfigPage 组件复用 ConfigPage 的模式，保持 UI 一致性

## 测试覆盖

### 后端（81 个测试全部通过）

**test_gpt_image_provider.py (5 tests)**
1. `test_gpt_provider_is_available_with_key` — 有 key 时可用
2. `test_gpt_provider_not_available_without_key` — 无 key 时不可用
3. `test_gpt_provider_generates_image` — Mock API 返回 base64 PNG，验证文件写入+metadata
4. `test_gpt_provider_error_without_key` — 无 key 时 generate() 抛出 RuntimeError
5. `test_gpt_provider_path_sanitized` — 特殊字符路径清理

### 前端

现有测试不受影响。

## 依赖与来源说明

本 PR 不引入新的第三方依赖。`httpx` 已在 PR5 中引入用于 OpenAI LLM 调用，本 PR 复用同一库调用图片 API。

## 接入真实 API 的步骤

1. 打开前端 → Image API 配置
2. 填入 Base URL 和 API Key（如使用第三方代理）
3. 选择模型（GPT Image 2 / DALL-E 3 / DALL-E 2）
4. 设置尺寸和画质
5. 点击 SAVE CONFIG
6. 在素材生成页选择 targetModel = GPT Image
7. COMPILE PROMPT → GENERATE ASSETS

无凭证时系统自动使用 Mock Provider，流程不受影响。
