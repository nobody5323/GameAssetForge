# PR14：七牛云 Kodo 云存储上传

## 新增/修改内容

### 后端
- **新增**：`backend/app/providers/qiniu_cloud_provider.py` — QiniuCloudProvider，基于七牛云 Python SDK 实现文件上传
- **新增**：`backend/tests/test_qiniu_cloud.py` — 10 个云配置 API + 七牛云 Provider + 服务选择测试
- **修改**：`backend/app/config.py` — 新增 `CloudRuntimeConfig` 运行时配置类，管理云存储凭证（Access Key / Secret Key / Bucket / 域名）
- **修改**：`backend/app/models/config_models.py` — 新增 `CloudProviderType`、`CloudConfigUpdate`、`CloudConfigResponse` 模型
- **修改**：`backend/app/routes/config_routes.py` — 新增 `GET/PUT /api/config/cloud` 路由
- **修改**：`backend/app/services/cloud_service.py` — 新增 `_create_cloud_provider()` 自动选择器（凭证就绪→七牛云，未配置→Mock 降级）
- **修改**：`backend/requirements.txt` — 新增 `qiniu==7.14.0`
- **修改**：`backend/tests/test_cloud_service.py` — 添加测试前配置重置逻辑

### 前端
- **新增**：`frontend/src/cloudConfig.js` — 云配置模块：Provider 选项、表单默认值、API 读写函数
- **修改**：`frontend/src/App.jsx` — 新增 "云存储配置" 导航页；新增 `CloudConfigPage` 组件（Mock/七牛云切换、凭证表单、使用说明）

## 功能描述

本 PR 在 Mock Cloud Provider 基础上接入七牛云 Kodo 真实云存储上传：

### 七牛云 Kodo Provider

- 使用七牛 Python SDK (`qiniu`) 进行 Token 认证上传
- 调用 `Auth.upload_token()` 生成上传凭证，`put_file()` 上传文件
- 上传 Key 格式：`{asset_id}/{filename}`
- 支持自定义 CDN 加速域名，构建公开访问 URL
- 未配置域名时，自动使用七牛云 30 天测试域名
- 无有效凭证时抛出明确的中文错误提示

### 前端云存储配置页

- 新增独立配置页 "云存储配置"
- 支持 Mock / 七牛云 Kodo Provider 切换
- 选择七牛云后展开：Access Key、Secret Key、Bucket、CDN 域名（可选）
- 凭证已配置时显示"清空当前凭证"选项
- 提供七牛云使用说明（注册、获取凭证、域名说明）
- 配置状态摘要（Provider / Bucket / 域名 / 凭证状态）

### Provider 选择机制

```
CloudService → _create_cloud_provider()
  └─ provider == "qiniu" + is_qiniu_available()
       ├─ True  → QiniuCloudProvider
       └─ False → MockCloudProvider (降级)
```

## 实现思路

- `QiniuCloudProvider` 继承 `CloudProvider` 抽象类（PR12），保持接口一致
- `CloudRuntimeConfig` 设计遵循 `LlmRuntimeConfig` / `ImageRuntimeConfig` 模式：env vars + local JSON 文件双层配置
- 密钥永不在 API 响应中返回（`public_response()` 不包含 accessKey/secretKey）
- `_create_cloud_provider()` 作为工厂函数，与 `AssetGenerationService._select_provider()` 模式一致
- 前端 CloudConfigPage 复用 ConfigPage / ImageConfigPage 的 LOAD/SAVE 模式

## 测试覆盖

### 后端（91 个测试全部通过）

**test_qiniu_cloud.py (10 tests)**

- TestCloudConfigAPI (4 tests)：
  1. `test_get_cloud_config_returns_defaults` — 默认返回 Mock Provider
  2. `test_update_cloud_config_switches_to_qiniu` — 切换到七牛云后返回正确配置
  3. `test_clear_credentials` — 清空凭证回归 Mock
  4. `test_secret_key_not_returned` — 密钥不在 API 响应中泄露

- TestQiniuCloudProvider (3 tests)：
  1. `test_qiniu_provider_upload_success` — Mock put_file 验证上传流程和 URL 构建
  2. `test_qiniu_provider_missing_file` — 源文件不存在抛出 FileNotFoundError
  3. `test_qiniu_provider_no_credentials_raises` — 无凭证抛出中文 RuntimeError

- TestCloudServiceSelection (3 tests)：
  1. `test_cloud_service_uses_mock_by_default` — 默认使用 Mock
  2. `test_cloud_service_uses_qiniu_when_configured` — 凭证就绪时自动选择七牛云
  3. `test_cloud_service_falls_back_to_mock_without_credentials` — 凭证不足时降级 Mock

## 依赖与来源说明

本 PR 引入第三方依赖 `qiniu==7.14.0`（七牛云 Python SDK），用于 Kodo 对象存储的 token 认证和文件上传。SDK 仅在后端 Provider 层使用，不影响其他模块。

## 接入真实七牛云的步骤

1. 注册[七牛云账号](https://www.qiniu.com/)并开通对象存储 Kodo 服务
2. 在七牛云控制台创建 Bucket，获取 Access Key 和 Secret Key
3. 打开前端 → 云存储配置
4. 选择 Provider = 七牛云 Kodo
5. 填入 Access Key、Secret Key、Bucket 名称
6. （可选）填入 CDN 加速域名，留空使用 30 天测试域名
7. 点击 SAVE CONFIG
8. 在导出交付页选择 Generation → UPLOAD TO CLOUD
9. 上传成功后在素材库可查看 cloudUrl

未配置真实凭证时系统自动使用 Mock Provider，上传返回 `cloud://mock/...` 格式模拟 URL。
