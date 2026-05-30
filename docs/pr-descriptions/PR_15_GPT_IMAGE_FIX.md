# PR15：gpt-image-2 兼容第三方中转站 + 素材生成容错

## 新增/修改内容

### 后端
- **修改**：`backend/app/providers/gpt_image_provider.py` — 重构 API 调用层
  - 模型分发：`dall-e-*` → Images API，`gpt-image-2` → Chat Completions API
  - 提取 `_httpx_post()` 公共方法，包含网络错误捕获和自动重试
  - 新增 `_download_image()` 方法，下载中转站返回的图片 URL
  - 新增 `_extract_image_url()` 模块函数，支持 Markdown 图片语法和裸 URL
  - 请求格式兼容：`content` 从数组格式改为简单字符串格式
  - 请求头添加 `Connection: close` 防止 keep-alive 异常
  - 网络断开自动重试 1 次，间隔 5s

- **修改**：`backend/app/services/asset_generation_service.py` — 素材生成容错
  - 每个素材独立 try/except，一个失败不影响其他素材
  - `AssetGenerateResponse` 新增 `errors` 字段返回失败详情
  - 全部失败仍抛 RuntimeError（保持已有行为）

- **修改**：`backend/app/models/asset_models.py` — response 模型扩展
  - `AssetGenerateResponse` 新增 `errors: list[str]` 字段

- **修改**：`backend/app/config.py` — 超时调整
  - 图片 API 超时从 120s 提升到 300s，适配 gpt-image-2 慢生成

- **修改**：`backend/tests/test_gpt_image_provider.py` — 测试更新
  - 新增 `test_gpt_image2_generates_image` — Chat Completions + Markdown URL 格式
  - 新增 `test_api_error_returns_runtime_error_with_body` — API 错误体透传
  - Mock 调整为匹配中转站实际返回格式（Markdown 图片链接）

### 前端
- **修改**：`frontend/src/App.jsx` — 素材生成页
  - 生成结果标题显示失败计数（如"已生成 1 个素材，1 个失败"）
  - 素材网格下方显示失败详情（红色提示框，列出每个失败的素材和原因）

- **修改**：`frontend/src/assetGeneration.js` — 摘要函数
  - `summarizeGeneratedAssets` 包含失败数量

### 脚本
- **修改**：`start-dev.bat` / `start-dev.sh` — 修复后端启动命令
  - `app.main:create_app --factory` → `app.main:app`（更稳定的模块级引用）

## 功能描述

### gpt-image-2 第三方中转站兼容

**问题背景**：gpt-image-2 通过 Chat Completions API 调用，但第三方中转站（如 micuapi.ai）的返回格式与 OpenAI 官方不同：

| 来源 | 格式 | 图片数据位置 |
|------|------|------------|
| OpenAI 官方 | `message.annotations[].image.b64_json` | base64 内联 |
| 中转站（micuapi.ai） | `message.content` | Markdown 图片链接 → 需下载 |

**解决方案**：

1. **正确的 API 端点** — 根据模型名自动分发：
   ```
   dall-e-2 / dall-e-3 → POST /v1/images/generations  (Images API)
   gpt-image-2         → POST /v1/chat/completions     (Chat Completions API)
   ```

2. **多格式响应解析** — `_call_chat_api()` 按优先级探测：
   ```
   ① message.annotations[].image.b64_json  (OpenAI 官方)
   ② message.content → 提取 Markdown URL   (第三方中转站)
      → HTTP 下载图片 → base64 编码 → 保存 PNG
   ```

3. **请求格式兼容** — `content` 使用简单字符串而非数组格式，确保老旧 API 代理兼容

4. **连接稳定性** — `Connection: close` 防止 keep-alive 异常；网络断开自动重试 1 次（间隔 5s）

### 素材生成容错

**问题背景**：生成多个素材时（如角色 + 敌人 + 物品），如果某个素材的 API 调用失败（超时/连接断开/格式异常），原本会导致整个请求失败，已成功的素材也丢失。

**解决方案**：`AssetGenerationService.generate()` 中每个素材独立 try/except：
```
素材 1 (角色)  → 成功 ✓ → 入库
素材 2 (敌人)  → 失败 ✗ → 记录到 errors[]
素材 3 (物品)  → 成功 ✓ → 入库
─────────────────────────
返回：2 个素材 + 1 个错误记录
全部失败才抛 RuntimeError
```

**前端展示**：
- 顶部：`已生成 2 个素材，1 个失败：gen_xxx`
- 底部红色提示框：`character/亚丝娜: Chat Completions API returned unexpected format...`

### 图片 API 错误透传

**问题背景**：API 错误被泛化为 `500 Internal Server Error`，用户看不到中转站返回的真正原因。

**解决方案**：
- `_raise_on_api_error()` — HTTP 错误响应时读取 `response.text` 并附加到错误消息
- `_httpx_post()` — 捕获 `httpx.RequestError` 转为 `RuntimeError` → 路由层返回 502
- 前端错误显示：拿到完整错误信息展示给用户

## 实现思路

- **API 分发**：在 `generate()` 中检查 `image_model` 前缀（`dall-e` vs 其他），选择对应端点，未来新增模型（如 DALL-E 4、Sora image 等）无需改动调用侧
- **响应格式探测**：先尝试 annotations → 再尝试 content URL，失败时把完整响应内容打印到错误消息中方便调试
- **网络重试**：`_httpx_post()` 重试逻辑只拦截 `httpx.RequestError`（网络层），不拦截 `RuntimeError`（业务/认证层），避免重复执行无效请求
- **容错设计**：服务层逐素材 try/except，`AssetGenerateResponse.errors` 为可选字段（空列表时不展示），向后兼容

## 测试覆盖

### 后端（gpt_image_provider：7 个测试全部通过）

- `test_gpt_provider_is_available_with_key` — 有密钥时可用
- `test_gpt_provider_not_available_without_key` — 无密钥时不可用
- `test_dalle_generates_image` — DALL-E 走 Images API
- `test_dalle_error_without_key` — 无密钥抛 RuntimeError
- `test_dalle_path_sanitized` — 路径特殊字符清理
- `test_gpt_image2_generates_image` — **新增**：gpt-image-2 走 Chat Completions + Markdown URL 格式
- `test_api_error_returns_runtime_error_with_body` — **新增**：API 错误体正确透传（含中文）

### 前端（17 个测试全部通过）

## 认证说明

gpt-image-2 通过配置的 `IMAGE_GEN_API_KEY` 认证。中转站（`baseUrl`）和模型（`imageModel`）在前端 Image API 配置页独立管理。无密钥或中转站不可用时自动降级为 Mock Provider。
