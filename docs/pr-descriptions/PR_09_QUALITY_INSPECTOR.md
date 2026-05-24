# PR 9: Quality Inspector 质量检查器

## 新增/修改内容

- 新增 `backend/app/models/quality_models.py`
  - `QualityCheck`：单项检查结果（name, label, passed, message, score, maxScore）
  - `AssetQualityReport`：单个素材的质量报告（assetId, checks[], totalScore, maxScore）
  - `GenerationQualityReport`：整个 generation 的汇总报告（generationId, assets[], overallScore, passCount, failCount）
- 新增 `backend/app/services/quality_service.py`
  - `QualityService.inspect_asset(asset_id)` — 对单个素材执行 7 项质量检查
  - `QualityService.inspect_generation(generation_id)` — 汇总整个 generation 的质量报告
  - 内置 PNG IHDR 解析函数 `_read_png_dimensions()`，不依赖 Pillow
- 新增 `backend/app/routes/quality_routes.py`
  - `POST /api/quality/inspect/{asset_id}` — 检查单个素材
  - `GET /api/quality/report/{generation_id}` — 获取 generation 汇总报告
- `backend/app/main.py` 注册 quality router
- 新增 `backend/tests/test_quality_inspector.py`（11 个测试）

## 功能描述

本 PR 实现后端质量检查器。对每个素材自动执行 7 项检查，满分 100 分：

| # | 检查项 | 满分 | 说明 |
|---|--------|------|------|
| 1 | 文件格式 | 15 | 验证 PNG 签名 `\x89PNG\r\n\x1a\n`，文件存在且可读 |
| 2 | 图片尺寸 | 15 | 解析 IHDR chunk 读取宽高，范围 16–4096 为合格 |
| 3 | 命名规范 | 10 | snake_case：无空格、无大写、无特殊字符 |
| 4 | 分类目录 | 15 | 文件路径包含 `/{assetType}/` 目录段 |
| 5 | Prompt 记录 | 15 | finalPrompt 非空且 ≥ 20 字符 |
| 6 | Manifest 就绪 | 15 | id、assetName、assetType、localPath 均已填充 |
| 7 | 云端就绪 | 15 | cloudUrl 已设置（PR12 接入云端上传后生效） |

**评分逻辑：**
- 每项检查独立打分，总分 = 各项得分之和
- 通过的素材（totalScore ≥ 60）计入 passCount，否则计入 failCount
- generation 汇总报告的 overallScore = 各素材 totalScore 的平均值

**目前 mock 素材的典型得分：85/100**（所有检查通过，仅 cloudUrl 未设置扣 15 分）

## 实现思路

- PNG 尺寸解析使用标准库 `struct` 读取 IHDR chunk 前 8 字节（width, height），不依赖 Pillow。
- 检查项设计为独立函数，每个返回 `QualityCheck` 结构，便于后续增减检查项。
- 命名规范检查使用正则：`[A-Z]` 检测大写、`[^a-z0-9_]` 检测特殊字符、空格检测。
- 文件不存在时，格式和尺寸两项均返回 0 分并给出明确错误信息。
- `inspect_generation` 对不存在的 generationId 返回空报告（assetCount=0），不抛 404，方便前端处理边界情况。

## 测试方式

后端：

```bash
cd backend
python -m pytest
```

已验证：

```text
30 passed
```

新增 11 个质量检查测试覆盖：

- PNG 尺寸读取（合法 PNG 返回 64x64）
- 非 PNG 文件抛出 ValueError
- 单素材检查：全部 7 项得分分布、总分计算（85/100）
- Generation 汇总报告：2 个素材的 passCount/failCount/overallScore
- 不存在的 generation 返回空报告
- API 端点：`POST /api/quality/inspect/{id}` 返回完整报告
- API 端点：不存在素材返回 404
- API 端点：`GET /api/quality/report/{genId}` 返回汇总
- 命名规范：空格和大写字母被标记为不通过
- 文件缺失：格式检查返回 0 分

接口人工验证：

```bash
# 先生成素材
curl -X POST http://127.0.0.1:8000/api/assets/generate \
  -H "Content-Type: application/json" \
  -d '{"projectName":"Test","gameType":"platformer","style":"pixel_art","theme":"test","description":"test","targetModel":"mock_seed","promptMode":"normal","assets":[{"type":"character","name":"hero","description":"main character"}]}'

# 获取 assetId 后检查
curl -X POST http://127.0.0.1:8000/api/quality/inspect/{asset_id}

# 查看 generation 汇总
curl http://127.0.0.1:8000/api/quality/report/{generation_id}
```

## 依赖与来源说明

- 不新增第三方依赖。
- PNG 解析使用 Python 标准库 `struct`。
- 复用 PR7 的 `AssetRepository` 读取素材记录。
- 复用 PR6 的 `MockImageProvider` 生成测试用 PNG。
