# PR 6: Mock Image Provider

## 新增/修改内容

- 新增 `backend/app/models/asset_models.py`
  - 定义 `ImageGenerationRequest`
  - 定义 `GeneratedImage`
- 新增 `backend/app/providers/image_provider.py`
  - 定义统一 `ImageProvider.generate()` 抽象接口
- 新增 `backend/app/providers/mock_image_provider.py`
  - 实现 `MockImageProvider`
  - 自动准备 mock PNG 种子素材
  - 将素材复制到本地 generated-assets 运行时目录
  - 返回本地路径和 provider metadata
- 新增 `backend/app/utils/png_writer.py`
  - 使用 Python 标准库生成最小 PNG 文件
- 新增 `backend/tests/test_mock_image_provider.py`
  - 覆盖生成路径、mock metadata、种子素材复用、未知素材类型 slug 清理

## 功能描述

本 PR 实现素材生成 Provider 层的 mock 能力。它不调用真实生图 API，也不需要 API Key。

调用 `MockImageProvider.generate()` 后，系统会：

- 根据 `assetType` 准备本地 mock PNG 种子素材；
- 将种子素材复制到当前 generation 对应目录；
- 返回 `assetName`、`assetType`、`localPath`、`provider`、`metadata`；
- metadata 包含 `promptHash`、`promptVersion`、源素材路径、尺寸和 mock 标记。

本 PR 不新增对外 HTTP 生成接口。PR7 会把 Prompt Compiler、Mock Provider 和 Asset Repository 串起来，实现 `POST /api/assets/generate`。

## 实现思路

- 使用抽象基类 `ImageProvider` 固定 provider 接口，后续 OpenAI、Stable Diffusion、Qiniu 等 provider 可以复用同一调用形状。
- 使用 `ImageGenerationRequest` 作为 provider 输入，避免后续服务层传散乱参数。
- 使用 `GeneratedImage` 作为 provider 输出，保证路径和 metadata 可被 Asset Repository 持久化。
- Mock PNG 不依赖 Pillow，使用标准库 `struct`、`zlib` 写入合法 PNG，降低安装和比赛演示风险。
- 运行时文件写入 `backend/runtime/storage/...`，该目录已被 `.gitignore` 忽略，避免测试和演示生成物进入仓库。
- 文件名和目录名通过 slug 清理，保证空格、感叹号等输入不会破坏路径结构。

## 测试方式

后端：

```bash
cd backend
python -m pytest
```

已验证：

```text
13 passed
```

重点测试：

- `MockImageProvider.generate()` 返回 provider 为 `mock`；
- 生成文件路径形如 `runtime/storage/generated-assets/{generationId}/{assetType}/{assetName}.png`；
- 生成文件是合法 PNG；
- 同一素材类型复用同一 mock seed；
- 未知素材类型会生成可用 fallback PNG；
- metadata 包含 `promptHash`、`promptVersion`、尺寸和 mock 标记。

## 依赖与来源说明

- 本 PR 不新增第三方依赖。
- PNG 写入使用 Python 标准库 `struct`、`zlib`、`pathlib`。
- Mock Provider 不调用真实生图 API，不读取 OpenAI Key。
