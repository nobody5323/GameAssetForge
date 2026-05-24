# PR 9: Quality Inspector 质量检查器

## 新增/修改内容

- 新增 `backend/app/models/quality_models.py`
  - `QualityCheck`：单项检查结果（扣分制：score=扣分, maxScore=最多扣分, passed=无扣分即为通过）
  - `AssetQualityReport`：单个素材的质量报告（totalScore=100-总扣分）
  - `GenerationQualityReport`：整个 generation 的汇总报告（passCount≥60分, failCount<60分）
- 新增 `backend/app/services/quality_service.py`
  - **扣分制评分**：满分 100，逐项扣分，最终得分 = 100 - 总扣分（下限 0）
  - 6 项常规检查 + 1 项致命检查（非 PNG 直接归零）
  - 内置 PNG IHDR 解析（width/height/color_type）、纯色图检测、2 的幂判断
- 新增 `backend/app/routes/quality_routes.py`
  - `POST /api/quality/inspect/{asset_id}` — 检查单个素材
  - `GET /api/quality/report/{generation_id}` — 获取 generation 汇总报告
- `backend/app/main.py` 注册 quality router
- 新增 `backend/tests/test_quality_inspector.py`（15 个测试）

## 功能描述

本 PR 实现后端质量检查器，采用**扣分制**评分（满分 100，逐项扣分）。设计参考 T2I-CompBench（属性绑定/对象关系/复杂组合）、GenEval（对象存在/数量/颜色/位置对齐）、Intel CGVQM（游戏画面实时质量度量）等图像质量评估研究。

### 评分类比

| 研究 | 核心维度 | 本 PR 对应检查 |
|------|---------|---------------|
| T2I-CompBench | 属性绑定、对象关系、复杂组合 | Prompt 质量（风格关键词、主体描述） |
| GenEval | 对象存在、数量、颜色、位置 | Prompt 质量（名称匹配）、纯色图检测 |
| Intel CGVQM | 分辨率、纹理、伪影 | 尺寸规格（分级扣分、2的幂/16对齐） |

### 检查项与扣分规则

| # | 检查项 | 最多扣分 | 扣分规则 |
|---|--------|---------|---------|
| 🚫 | **PNG 合规（致命）** | 100 | 非 PNG / 文件不存在 / < 70 bytes → 直接 0 分 |
| 1 | **尺寸规格** | 30 | <64px 扣 30、<128px 扣 25、<256px 扣 18、>4096px 扣 20；非 2 的幂扣 10；非 16 倍数扣 5；**纯色图扣 15**（mock 检测） |
| 2 | **命名规范** | 20 | 含空格扣 8、含大写扣 5、含特殊字符扣 10、数字开头扣 3、>40 字符扣 3 |
| 3 | **目录分类** | 20 | 路径缺少类型目录扣 20、层级过浅扣 10 |
| 4 | **Prompt 质量** | 25 | 空 prompt 扣 25、< 20 字符扣 25、< 50 字符扣 15、< 100 字符扣 8；缺风格关键词扣 8；未提及素材名扣 5 |
| 5 | **元数据完整** | 15 | 缺 ID 扣 8、缺 generationId 扣 5、缺 provider 扣 5、缺 promptVersion 扣 5 |
| 6 | **交付就绪** | 20 | 无 cloudUrl 扣 15、mock provider 扣 10、manifest 缺字段扣 8 |

### 得分差异示例

| 素材类型 | 典型得分 | 扣分原因 |
|---------|---------|---------|
| 接近完美（256x256 + cloudUrl + openai） | **95–100** | 几乎无扣分 |
| Mock 64x64 纯色（无 cloudUrl） | **35–55** | 尺寸 -18~25 + 纯色 -15 + mock -10 + cloudUrl -15 |
| Mock + 命名不规范（Bad Name!） | **15–35** | 额外命名扣分 -15~20 |
| 非 PNG 文件 | **0** | 致命检查直接归零 |

## 实现思路

- **扣分制**：每项独立累计扣分，`totalScore = max(0, 100 - sum(所有扣分))`。通过阈值 60 分。
- **PNG 致命检查**：非 PNG 文件直接归零，不继续检查其他项，避免无意义的后续分析。
- **纯色图检测**：解析 IDAT chunk 解压后在图像上、中、下三行 + 左、中、右三列采样 9 个像素点，RGB 全部一致则判定为 mock 纯色素材。
- **尺寸分级**：参考游戏资产最佳实践——推荐 256px+、2 的幂（GPU 友好）、16 倍数（tile-map 对齐）。
- **PNG 解析全标准库**：不依赖 Pillow，使用 `struct` + `zlib` 解析 IHDR/IDAT。
- **Generation 汇总**：`overallScore` = 所有素材得分的平均值；`passCount`/`failCount` 以 60 分为界。

## 测试方式

后端：

```bash
cd backend
python -m pytest
```

已验证：

```text
34 passed
```

新增 15 个质量检查测试覆盖：

- PNG 尺寸读取（64x64）
- 非 PNG 文件抛出异常
- 2 的幂判断（正例/反例）
- 纯色图检测（mock PNG → True）
- **mock 素材得分 35-55**（尺寸+纯色+mock+cloudUrl 扣分）
- **完美素材得分 ≥ 95**（256x256 棋盘格+cloudUrl+openai）
- 命名不规范比规范素材得分更低
- 两个素材得分有差异
- PNG 致命检查（非 PNG → 0 分）
- 文件缺失 → 0 分
- API 返回扣分制报告
- 404 未知素材
- Generation 汇总端点

接口人工验证：

```bash
# 先生成素材
curl -X POST http://127.0.0.1:8000/api/assets/generate \
  -H "Content-Type: application/json" \
  -d '{"projectName":"Test","gameType":"platformer","style":"pixel_art","theme":"test","description":"test","targetModel":"mock_seed","promptMode":"normal","assets":[{"type":"character","name":"hero","description":"main character"}]}'

# 质量检查
curl -X POST http://127.0.0.1:8000/api/quality/inspect/{asset_id}

# Generation 汇总
curl http://127.0.0.1:8000/api/quality/report/{generation_id}
```

## 依赖与来源说明

- 不新增第三方依赖。
- PNG 解析使用 Python 标准库 `struct`、`zlib`。
- 评分维度参考 T2I-CompBench (NeurIPS 2023)、GenEval (Meta 2023)、Intel CGVQM (2025)。
- 复用 PR7 的 `AssetRepository` 读取素材记录。
